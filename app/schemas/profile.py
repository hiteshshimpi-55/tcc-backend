import uuid

from pydantic import BaseModel, Field

from app.db.models.enums import StartupRole
from app.db.models.voice import EmojiUsage, WritingStyle
from app.schemas.voice import VoiceProfileResponse


class ProfileOrganizationSummary(BaseModel):
    id: uuid.UUID
    name: str


class ProfileUserResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None
    avatar_url: str | None
    role_title: str | None
    bio: str | None
    startup_role: StartupRole | None
    profile_completed: bool
    onboarding_completed: bool


class ProfileResponse(BaseModel):
    user: ProfileUserResponse
    voice: VoiceProfileResponse
    organization: ProfileOrganizationSummary | None = None


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    bio: str | None = Field(default=None, max_length=5000)
    startup_role: StartupRole
    writing_style: WritingStyle
    emoji_usage: EmojiUsage
    preferred_tones: list[str] = Field(min_length=1)
    specialty_prompt: str | None = Field(default=None, max_length=5000)
