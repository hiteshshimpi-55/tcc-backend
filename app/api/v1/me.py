from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth import get_token_claims
from app.api.auth_jwt import SupabaseTokenClaims
from app.db.session import get_db
from app.schemas.base import success_response
from app.schemas.profile import UpdateProfileRequest
from app.schemas.user import MeResponse, SetActiveOrganizationRequest, UpdateMeRequest
from app.services import profile_service, user_service

router = APIRouter()


@router.get("/me")
async def get_me(
    request: Request,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    payload = MeResponse(user=user_service.build_user_response(db, user))
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")


@router.get("/me/profile")
async def get_profile(
    request: Request,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    payload = profile_service.get_profile(db, user)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")


@router.patch("/me/profile")
async def update_profile(
    request: Request,
    body: UpdateProfileRequest,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    payload = profile_service.update_profile(db, user, body)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")


@router.patch("/me")
async def update_me(
    request: Request,
    body: UpdateMeRequest,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    user = user_service.update_me(db, user, body)
    payload = MeResponse(user=user_service.build_user_response(db, user))
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")


@router.patch("/me/active-organization")
async def set_active_organization(
    request: Request,
    body: SetActiveOrganizationRequest,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    user = user_service.set_active_organization(db, user, body.organization_id)
    payload = MeResponse(user=user_service.build_user_response(db, user))
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")
