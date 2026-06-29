from pydantic import BaseModel, Field

from app.db.models.voice import EmojiUsage, WritingStyle


class VoiceProfileResponse(BaseModel):
    writing_style: WritingStyle | None
    emoji_usage: EmojiUsage | None
    preferred_tones: list[str]
    specialty_prompt: str | None

    model_config = {"from_attributes": True}


class UpdateVoiceProfileRequest(BaseModel):
    writing_style: WritingStyle
    emoji_usage: EmojiUsage
    preferred_tones: list[str] = Field(min_length=1)
    specialty_prompt: str | None = Field(default=None, max_length=5000)
