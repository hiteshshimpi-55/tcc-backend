from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid
from app.db.models.enums import StartupRole

if TYPE_CHECKING:
    from app.db.models.organization import Organization, OrganizationMember
    from app.db.models.voice import UserVoiceProfile


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    supabase_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    startup_role: Mapped[StartupRole | None] = mapped_column(
        Enum(StartupRole, name="startup_role", native_enum=False),
        nullable=True,
    )
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    memberships: Mapped[list[OrganizationMember]] = relationship(
        "OrganizationMember",
        back_populates="user",
        foreign_keys="OrganizationMember.user_id",
    )
    owned_organizations: Mapped[list[Organization]] = relationship(
        "Organization",
        back_populates="owner",
        foreign_keys="Organization.owner_id",
    )
    voice_profile: Mapped[UserVoiceProfile | None] = relationship(
        "UserVoiceProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
