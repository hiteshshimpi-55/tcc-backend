import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.enums import StartupRole
from app.db.models.user import User
from app.db.models.voice import EmojiUsage, WritingStyle
from app.schemas.profile import UpdateProfileRequest
from app.schemas.user import UpdateMeRequest
from app.schemas.voice import UpdateVoiceProfileRequest
from app.services import profile_service, user_service, voice_service


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_update_me_sets_profile_completed(db_session: Session):
    user = User(
        supabase_id=uuid.uuid4(),
        email="user@example.com",
        full_name="User",
    )
    db_session.add(user)
    db_session.commit()

    updated = user_service.update_me(
        db_session,
        user,
        UpdateMeRequest(
            full_name="User Name",
            bio="Builder",
            startup_role=StartupRole.founder,
        ),
    )

    assert updated.profile_completed is True
    assert updated.role_title == "Founder"
    assert updated.startup_role == StartupRole.founder


def test_create_organization_with_profile_fields(db_session: Session):
    user = User(supabase_id=uuid.uuid4(), email="owner@example.com", full_name="Owner")
    db_session.add(user)
    db_session.commit()

    from app.schemas.user import CreateOrganizationRequest

    org = user_service.create_organization(
        db_session,
        user,
        "Acme",
        CreateOrganizationRequest(
            name="Acme",
            category="SaaS",
            description="We build tools",
            target_audience="CTOs",
            major_platforms=["linkedin"],
        ),
    )

    assert org.category == "SaaS"
    assert org.description == "We build tools"
    assert org.major_platforms == ["linkedin"]


def test_update_voice_profile_sets_onboarding_completed(db_session: Session):
    user = User(
        supabase_id=uuid.uuid4(),
        email="user@example.com",
        full_name="User",
        profile_completed=True,
    )
    db_session.add(user)
    db_session.commit()

    voice_service.update_voice_profile(
        db_session,
        user,
        UpdateVoiceProfileRequest(
            writing_style=WritingStyle.concise,
            emoji_usage=EmojiUsage.none,
            preferred_tones=["technical"],
            specialty_prompt="Keep it practical",
        ),
    )

    db_session.refresh(user)
    assert user.onboarding_completed is True
    profile = voice_service.get_voice_profile(db_session, user)
    assert profile.writing_style == WritingStyle.concise
    assert profile.preferred_tones == ["technical"]

    row = db_session.scalar(select(User).where(User.id == user.id))
    assert row is not None
    assert row.onboarding_completed is True


def test_get_profile_returns_user_voice_and_organization(db_session: Session):
    user = User(
        supabase_id=uuid.uuid4(),
        email="user@example.com",
        full_name="User",
    )
    db_session.add(user)
    db_session.commit()

    from app.schemas.user import CreateOrganizationRequest

    org = user_service.create_organization(
        db_session,
        user,
        "Acme",
        CreateOrganizationRequest(name="Acme"),
    )

    profile = profile_service.get_profile(db_session, user)

    assert profile.user.full_name == "User"
    assert profile.voice.writing_style is None
    assert profile.organization is not None
    assert profile.organization.id == org.id
    assert profile.organization.name == "Acme"


def test_update_profile_persists_personal_and_voice(db_session: Session):
    user = User(
        supabase_id=uuid.uuid4(),
        email="user@example.com",
        full_name="User",
    )
    db_session.add(user)
    db_session.commit()

    updated = profile_service.update_profile(
        db_session,
        user,
        UpdateProfileRequest(
            full_name="User Name",
            bio="Builder",
            startup_role=StartupRole.engineering,
            writing_style=WritingStyle.concise,
            emoji_usage=EmojiUsage.minimal,
            preferred_tones=["technical"],
            specialty_prompt="Keep it practical",
        ),
    )

    assert updated.user.profile_completed is True
    assert updated.user.onboarding_completed is True
    assert updated.user.role_title == "Engineering"
    assert updated.voice.writing_style == WritingStyle.concise
    assert updated.voice.preferred_tones == ["technical"]
