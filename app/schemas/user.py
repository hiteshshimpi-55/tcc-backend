import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import StartupRole
from app.db.models.organization import OrganizationRole


class OrganizationSummary(BaseModel):
    id: uuid.UUID
    name: str
    role: OrganizationRole

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    supabase_id: uuid.UUID
    email: str | None
    full_name: str | None
    avatar_url: str | None
    active_organization_id: uuid.UUID | None
    role_title: str | None
    bio: str | None
    startup_role: StartupRole | None
    profile_completed: bool
    onboarding_completed: bool
    organizations: list[OrganizationSummary] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserResponse


class UpdateMeRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    bio: str | None = Field(default=None, max_length=5000)
    startup_role: StartupRole | None = None


class SetActiveOrganizationRequest(BaseModel):
    organization_id: uuid.UUID


class OrganizationProfileFields(BaseModel):
    category: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    target_audience: str | None = Field(default=None, max_length=2000)
    major_platforms: list[str] = Field(default_factory=list)


class CreateOrganizationRequest(OrganizationProfileFields):
    name: str = Field(min_length=1, max_length=200)


class UpdateOrganizationRequest(OrganizationProfileFields):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    category: str | None
    description: str | None
    target_audience: str | None
    major_platforms: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str | None
    full_name: str | None
    role: OrganizationRole

    model_config = {"from_attributes": True}


class CreateInviteRequest(BaseModel):
    role: OrganizationRole = OrganizationRole.member
    expires_at: datetime | None = None
    max_uses: int | None = Field(default=None, ge=1)


class InviteResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    role: OrganizationRole
    expires_at: datetime | None
    max_uses: int | None
    use_count: int
    revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JoinOrganizationRequest(BaseModel):
    code: str = Field(min_length=4, max_length=8)
