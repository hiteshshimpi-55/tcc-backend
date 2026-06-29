from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.db.models.user import User


class WritingStyle(enum.StrEnum):
    concise = "concise"
    detailed = "detailed"
    opinionated = "opinionated"


class EmojiUsage(enum.StrEnum):
    none = "none"
    minimal = "minimal"
    expressive = "expressive"


class UserVoiceProfile(Base, TimestampMixin):
    __tablename__ = "user_voice_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    writing_style: Mapped[WritingStyle | None] = mapped_column(
        Enum(WritingStyle, name="writing_style", native_enum=False),
        nullable=True,
    )
    emoji_usage: Mapped[EmojiUsage | None] = mapped_column(
        Enum(EmojiUsage, name="emoji_usage", native_enum=False),
        nullable=True,
    )
    preferred_tones: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    specialty_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="voice_profile")
