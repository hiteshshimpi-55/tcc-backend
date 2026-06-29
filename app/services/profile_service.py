from sqlalchemy.orm import Session

from app.db.models.organization import Organization
from app.db.models.user import User
from app.schemas.profile import (
    ProfileOrganizationSummary,
    ProfileResponse,
    ProfileUserResponse,
    UpdateProfileRequest,
)
from app.schemas.user import UpdateMeRequest
from app.schemas.voice import UpdateVoiceProfileRequest
from app.services import user_service, voice_service


def _build_profile_user(user: User) -> ProfileUserResponse:
    return ProfileUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role_title=user.role_title,
        bio=user.bio,
        startup_role=user.startup_role,
        profile_completed=user.profile_completed,
        onboarding_completed=user.onboarding_completed,
    )


def _active_organization(db: Session, user: User) -> ProfileOrganizationSummary | None:
    if user.active_organization_id is None:
        return None
    org = db.get(Organization, user.active_organization_id)
    if org is None:
        return None
    return ProfileOrganizationSummary(id=org.id, name=org.name)


def get_profile(db: Session, user: User) -> ProfileResponse:
    return ProfileResponse(
        user=_build_profile_user(user),
        voice=voice_service.get_voice_profile(db, user),
        organization=_active_organization(db, user),
    )


def update_profile(db: Session, user: User, body: UpdateProfileRequest) -> ProfileResponse:
    user = user_service.update_me(
        db,
        user,
        UpdateMeRequest(
            full_name=body.full_name,
            bio=body.bio,
            startup_role=body.startup_role,
        ),
    )
    voice_service.update_voice_profile(
        db,
        user,
        UpdateVoiceProfileRequest(
            writing_style=body.writing_style,
            emoji_usage=body.emoji_usage,
            preferred_tones=body.preferred_tones,
            specialty_prompt=body.specialty_prompt,
        ),
    )
    db.refresh(user)
    return get_profile(db, user)
