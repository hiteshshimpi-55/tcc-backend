from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header
from jwt import PyJWKClient

from app.api.auth_jwt import SupabaseTokenClaims
from app.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError


@lru_cache
def get_jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def decode_supabase_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    algorithm = header.get("alg", "HS256")
    decode_options = {"require": ["exp", "sub"]}
    decode_kwargs: dict[str, Any] = {
        "algorithms": [algorithm],
        "audience": "authenticated",
        "options": decode_options,
    }
    if settings.supabase_jwt_issuer:
        decode_kwargs["issuer"] = settings.supabase_jwt_issuer

    try:
        if algorithm in {"ES256", "RS256"}:
            jwks_url = settings.supabase_jwks_url
            if not jwks_url:
                raise UnauthorizedError(
                    "SUPABASE_URL is required to verify asymmetric Supabase JWTs"
                )
            signing_key = get_jwks_client(jwks_url).get_signing_key_from_jwt(token)
            return jwt.decode(token, signing_key.key, **decode_kwargs)

        if not settings.supabase_jwt_secret:
            raise UnauthorizedError("JWT verification is not configured")

        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options=decode_options,
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc


def claims_from_payload(payload: dict[str, Any]) -> SupabaseTokenClaims:
    user_metadata = payload.get("user_metadata") or {}
    return SupabaseTokenClaims(
        supabase_id=__import__("uuid").UUID(str(payload["sub"])),
        email=payload.get("email"),
        full_name=user_metadata.get("full_name"),
        avatar_url=user_metadata.get("avatar_url"),
    )


async def get_token_claims(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> SupabaseTokenClaims:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_supabase_token(token, settings)
    return claims_from_payload(payload)
