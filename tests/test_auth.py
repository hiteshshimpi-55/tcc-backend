import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from pydantic_settings import SettingsConfigDict

from app.api.auth import claims_from_payload, decode_supabase_token
from app.api.auth_jwt import SupabaseTokenClaims
from app.config import Settings
from app.core.exceptions import UnauthorizedError

TEST_SECRET = "test-jwt-secret-for-unit-tests-with-enough-length"


class AuthTestSettings(Settings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")


def make_auth_settings(
    jwt_secret: str = TEST_SECRET,
    supabase_url: str = "",
) -> AuthTestSettings:
    return AuthTestSettings(SUPABASE_JWT_SECRET=jwt_secret, SUPABASE_URL=supabase_url)


def make_token(
    *,
    sub: str | None = None,
    email: str = "user@example.com",
    secret: str = TEST_SECRET,
    expired: bool = False,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub or str(uuid.uuid4()),
        "email": email,
        "aud": "authenticated",
        "user_metadata": {"full_name": "Test User"},
        "exp": int((now - timedelta(hours=1) if expired else now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_decode_valid_token():
    token = make_token(email="alice@example.com")
    payload = decode_supabase_token(token, make_auth_settings())
    claims = claims_from_payload(payload)
    assert isinstance(claims, SupabaseTokenClaims)
    assert claims.email == "alice@example.com"
    assert claims.full_name == "Test User"


def test_decode_expired_token_raises():
    token = make_token(expired=True)
    with pytest.raises(UnauthorizedError):
        decode_supabase_token(token, make_auth_settings())


def test_decode_invalid_secret_raises():
    token = make_token()
    with pytest.raises(UnauthorizedError):
        decode_supabase_token(token, make_auth_settings(jwt_secret="wrong-secret"))


def test_decode_missing_bearer_secret_raises():
    token = make_token()
    with pytest.raises(UnauthorizedError):
        decode_supabase_token(token, make_auth_settings(jwt_secret=""))
