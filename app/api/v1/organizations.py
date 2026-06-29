import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth import get_token_claims
from app.api.auth_jwt import SupabaseTokenClaims
from app.db.session import get_db
from app.schemas.base import success_response
from app.schemas.user import (
    CreateInviteRequest,
    CreateOrganizationRequest,
    InviteResponse,
    JoinOrganizationRequest,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationSummary,
    UpdateOrganizationRequest,
)
from app.services import user_service

router = APIRouter()


def _current_user(
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
):
    return user_service.sync_user(db, claims)


@router.get("")
async def list_organizations(
    request: Request,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    orgs = user_service.list_organizations(db, user)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        [OrganizationSummary.model_validate(o).model_dump(mode="json") for o in orgs],
        request_id,
    ).model_dump(mode="json")


@router.post("")
async def create_organization(
    request: Request,
    body: CreateOrganizationRequest,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    org = user_service.create_organization(
        db,
        user,
        body.name,
        body,
    )
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        OrganizationResponse.model_validate(org).model_dump(mode="json"),
        request_id,
    ).model_dump(mode="json")


@router.post("/join")
async def join_organization(
    request: Request,
    body: JoinOrganizationRequest,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    org = user_service.join_organization(db, user, body.code)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        OrganizationResponse.model_validate(org).model_dump(mode="json"),
        request_id,
    ).model_dump(mode="json")


@router.get("/{organization_id}")
async def get_organization(
    request: Request,
    organization_id: uuid.UUID,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    org = user_service.get_organization(db, user, organization_id)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        OrganizationResponse.model_validate(org).model_dump(mode="json"),
        request_id,
    ).model_dump(mode="json")


@router.patch("/{organization_id}")
async def update_organization(
    request: Request,
    organization_id: uuid.UUID,
    body: UpdateOrganizationRequest,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    org = user_service.update_organization(db, user, organization_id, body.name, body)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        OrganizationResponse.model_validate(org).model_dump(mode="json"),
        request_id,
    ).model_dump(mode="json")


@router.get("/{organization_id}/members")
async def list_members(
    request: Request,
    organization_id: uuid.UUID,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    members = user_service.list_members(db, user, organization_id)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        [OrganizationMemberResponse.model_validate(m).model_dump(mode="json") for m in members],
        request_id,
    ).model_dump(mode="json")


@router.post("/{organization_id}/invites")
async def create_invite(
    request: Request,
    organization_id: uuid.UUID,
    body: CreateInviteRequest,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    invite = user_service.create_invite(
        db, user, organization_id, body.role, body.expires_at, body.max_uses
    )
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        InviteResponse.model_validate(invite).model_dump(mode="json"),
        request_id,
    ).model_dump(mode="json")


@router.get("/{organization_id}/invites")
async def list_invites(
    request: Request,
    organization_id: uuid.UUID,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    invites = user_service.list_invites(db, user, organization_id)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        [InviteResponse.model_validate(i).model_dump(mode="json") for i in invites],
        request_id,
    ).model_dump(mode="json")


@router.delete("/{organization_id}/invites/{invite_id}")
async def revoke_invite(
    request: Request,
    organization_id: uuid.UUID,
    invite_id: uuid.UUID,
    user: Annotated[Any, Depends(_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    invite = user_service.revoke_invite(db, user, organization_id, invite_id)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(
        InviteResponse.model_validate(invite).model_dump(mode="json"),
        request_id,
    ).model_dump(mode="json")
