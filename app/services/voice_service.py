from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.voice import EmojiUsage, UserVoiceProfile, WritingStyle
from app.schemas.voice import UpdateVoiceProfileRequest, VoiceProfileResponse


def _default_voice_profile() -> VoiceProfileResponse:
    return VoiceProfileResponse(
        writing_style=None,
        emoji_usage=None,
        preferred_tones=[],
        specialty_prompt=None,
    )


def build_voice_profile_response(profile: UserVoiceProfile | None) -> VoiceProfileResponse:
    if profile is None:
        return _default_voice_profile()
    return VoiceProfileResponse(
        writing_style=profile.writing_style,
        emoji_usage=profile.emoji_usage,
        preferred_tones=list(profile.preferred_tones or []),
        specialty_prompt=profile.specialty_prompt,
    )


def get_voice_profile(db: Session, user: User) -> VoiceProfileResponse:
    profile = db.scalar(select(UserVoiceProfile).where(UserVoiceProfile.user_id == user.id))
    return build_voice_profile_response(profile)


def update_voice_profile(
    db: Session, user: User, body: UpdateVoiceProfileRequest
) -> VoiceProfileResponse:
    profile = db.scalar(select(UserVoiceProfile).where(UserVoiceProfile.user_id == user.id))
    if profile is None:
        profile = UserVoiceProfile(user_id=user.id)
        db.add(profile)

    profile.writing_style = WritingStyle(body.writing_style)
    profile.emoji_usage = EmojiUsage(body.emoji_usage)
    profile.preferred_tones = list(body.preferred_tones)
    profile.specialty_prompt = body.specialty_prompt.strip() if body.specialty_prompt else None

    user.onboarding_completed = True
    db.commit()
    db.refresh(profile)
    return build_voice_profile_response(profile)
