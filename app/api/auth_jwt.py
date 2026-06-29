import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SupabaseTokenClaims:
    supabase_id: uuid.UUID
    email: str | None
    full_name: str | None
    avatar_url: str | None
