from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth import get_token_claims
from app.api.auth_jwt import SupabaseTokenClaims
from app.db.session import get_db
from app.schemas.base import success_response
from app.schemas.voice import UpdateVoiceProfileRequest
from app.services import user_service, voice_service

router = APIRouter()


@router.get("/me/voice-profile")
async def get_voice_profile(
    request: Request,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    payload = voice_service.get_voice_profile(db, user)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")


@router.patch("/me/voice-profile")
async def update_voice_profile(
    request: Request,
    body: UpdateVoiceProfileRequest,
    claims: Annotated[SupabaseTokenClaims, Depends(get_token_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user = user_service.sync_user(db, claims)
    payload = voice_service.update_voice_profile(db, user, body)
    request_id = getattr(request.state, "request_id", "unknown")
    return success_response(payload.model_dump(mode="json"), request_id).model_dump(mode="json")
