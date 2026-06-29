import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth_jwt import SupabaseTokenClaims
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.db.models.enums import StartupRole, startup_role_label
from app.db.models.invite import OrganizationInvite
from app.db.models.organization import Organization, OrganizationMember, OrganizationRole
from app.db.models.user import User
from app.schemas.user import (
    OrganizationMemberResponse,
    OrganizationProfileFields,
    OrganizationSummary,
    UpdateMeRequest,
    UserResponse,
)


def sync_user(db: Session, claims: SupabaseTokenClaims) -> User:
    user = db.scalar(select(User).where(User.supabase_id == claims.supabase_id))
    if user is None:
        user = User(
            supabase_id=claims.supabase_id,
            email=claims.email,
            full_name=claims.full_name,
            avatar_url=claims.avatar_url,
        )
        db.add(user)
    else:
        user.email = claims.email or user.email
        user.full_name = claims.full_name or user.full_name
        user.avatar_url = claims.avatar_url or user.avatar_url
    db.commit()
    db.refresh(user)
    return user


def get_user_memberships(db: Session, user_id: uuid.UUID) -> list[OrganizationSummary]:
    rows = db.execute(
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == user_id)
        .order_by(Organization.name)
    ).all()
    return [OrganizationSummary(id=org.id, name=org.name, role=role) for org, role in rows]


def build_user_response(db: Session, user: User) -> UserResponse:
    orgs = get_user_memberships(db, user.id)
    return UserResponse(
        id=user.id,
        supabase_id=user.supabase_id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        active_organization_id=user.active_organization_id,
        role_title=user.role_title,
        bio=user.bio,
        startup_role=user.startup_role,
        profile_completed=user.profile_completed,
        onboarding_completed=user.onboarding_completed,
        organizations=orgs,
    )


def _apply_org_profile(org: Organization, profile: OrganizationProfileFields) -> None:
    if profile.category is not None:
        org.category = profile.category.strip() or None
    if profile.description is not None:
        org.description = profile.description.strip() or None
    if profile.target_audience is not None:
        org.target_audience = profile.target_audience.strip() or None
    org.major_platforms = list(profile.major_platforms)


def _profile_is_complete(user: User) -> bool:
    return bool(user.full_name and user.startup_role)


def update_me(db: Session, user: User, body: UpdateMeRequest) -> User:
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.bio is not None:
        user.bio = body.bio.strip() or None
    if body.startup_role is not None:
        user.startup_role = StartupRole(body.startup_role)
        user.role_title = startup_role_label(user.startup_role)

    user.profile_completed = _profile_is_complete(user)
    db.commit()
    db.refresh(user)
    return user


def get_membership(
    db: Session, user_id: uuid.UUID, organization_id: uuid.UUID
) -> OrganizationMember | None:
    return db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
    )


def require_membership(
    db: Session, user_id: uuid.UUID, organization_id: uuid.UUID
) -> OrganizationMember:
    membership = get_membership(db, user_id, organization_id)
    if membership is None:
        raise ForbiddenError("You are not a member of this organization")
    return membership


def require_admin(
    db: Session, user_id: uuid.UUID, organization_id: uuid.UUID
) -> OrganizationMember:
    membership = require_membership(db, user_id, organization_id)
    if membership.role not in (OrganizationRole.owner, OrganizationRole.admin):
        raise ForbiddenError("Admin access required")
    return membership


def create_organization(
    db: Session,
    user: User,
    name: str,
    profile: OrganizationProfileFields | None = None,
) -> Organization:
    org = Organization(name=name.strip(), owner_id=user.id)
    if profile is not None:
        _apply_org_profile(org, profile)
    db.add(org)
    db.flush()
    db.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=OrganizationRole.owner,
        )
    )
    user.active_organization_id = org.id
    db.commit()
    db.refresh(org)
    return org


def list_organizations(db: Session, user: User) -> list[OrganizationSummary]:
    return get_user_memberships(db, user.id)


def get_organization(db: Session, user: User, organization_id: uuid.UUID) -> Organization:
    require_membership(db, user.id, organization_id)
    org = db.get(Organization, organization_id)
    if org is None:
        raise NotFoundError("Organization not found")
    return org


def update_organization(
    db: Session,
    user: User,
    organization_id: uuid.UUID,
    name: str | None = None,
    profile: OrganizationProfileFields | None = None,
) -> Organization:
    require_admin(db, user.id, organization_id)
    org = db.get(Organization, organization_id)
    if org is None:
        raise NotFoundError("Organization not found")
    if name is not None:
        org.name = name.strip()
    if profile is not None:
        _apply_org_profile(org, profile)
    db.commit()
    db.refresh(org)
    return org


def list_members(
    db: Session, user: User, organization_id: uuid.UUID
) -> list[OrganizationMemberResponse]:
    require_membership(db, user.id, organization_id)
    rows = db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == organization_id)
        .order_by(User.full_name, User.email)
    ).all()
    return [
        OrganizationMemberResponse(
            id=member.id,
            user_id=member.user_id,
            email=u.email,
            full_name=u.full_name,
            role=member.role,
        )
        for member, u in rows
    ]


def set_active_organization(db: Session, user: User, organization_id: uuid.UUID) -> User:
    require_membership(db, user.id, organization_id)
    user.active_organization_id = organization_id
    db.commit()
    db.refresh(user)
    return user


def _generate_invite_code(db: Session) -> str:
    for _ in range(10):
        code = secrets.token_hex(4).upper()
        existing = db.scalar(select(OrganizationInvite).where(OrganizationInvite.code == code))
        if existing is None:
            return code
    raise ValidationError("Could not generate invite code")


def create_invite(
    db: Session,
    user: User,
    organization_id: uuid.UUID,
    role: OrganizationRole,
    expires_at: datetime | None,
    max_uses: int | None,
) -> OrganizationInvite:
    require_admin(db, user.id, organization_id)
    if role == OrganizationRole.owner:
        raise ValidationError("Cannot invite as owner")
    invite = OrganizationInvite(
        organization_id=organization_id,
        code=_generate_invite_code(db),
        role=role,
        created_by=user.id,
        expires_at=expires_at,
        max_uses=max_uses,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def list_invites(db: Session, user: User, organization_id: uuid.UUID) -> list[OrganizationInvite]:
    require_admin(db, user.id, organization_id)
    return list(
        db.scalars(
            select(OrganizationInvite)
            .where(OrganizationInvite.organization_id == organization_id)
            .order_by(OrganizationInvite.created_at.desc())
        ).all()
    )


def revoke_invite(
    db: Session, user: User, organization_id: uuid.UUID, invite_id: uuid.UUID
) -> OrganizationInvite:
    require_admin(db, user.id, organization_id)
    invite = db.get(OrganizationInvite, invite_id)
    if invite is None or invite.organization_id != organization_id:
        raise NotFoundError("Invite not found")
    invite.revoked_at = datetime.now(UTC)
    db.commit()
    db.refresh(invite)
    return invite


def join_organization(db: Session, user: User, code: str) -> Organization:
    normalized = code.strip().upper()
    invite = db.scalar(select(OrganizationInvite).where(OrganizationInvite.code == normalized))
    if invite is None:
        raise NotFoundError("Invalid invite code")
    if invite.revoked_at is not None:
        raise ValidationError("This invite has been revoked")
    if invite.expires_at is not None and invite.expires_at < datetime.now(UTC):
        raise ValidationError("This invite has expired")
    if invite.max_uses is not None and invite.use_count >= invite.max_uses:
        raise ValidationError("This invite has reached its use limit")

    existing = get_membership(db, user.id, invite.organization_id)
    org = db.get(Organization, invite.organization_id)
    if org is None:
        raise NotFoundError("Organization not found")

    if existing is None:
        db.add(
            OrganizationMember(
                organization_id=invite.organization_id,
                user_id=user.id,
                role=invite.role,
            )
        )
        invite.use_count += 1

    user.active_organization_id = invite.organization_id
    db.commit()
    db.refresh(org)
    return org
