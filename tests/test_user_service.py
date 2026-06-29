import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth_jwt import SupabaseTokenClaims
from app.core.exceptions import ValidationError
from app.db.base import Base
from app.db.models.organization import OrganizationMember, OrganizationRole
from app.db.models.user import User
from app.services import user_service


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


def test_sync_user_creates_record(db_session: Session):
    claims = SupabaseTokenClaims(
        supabase_id=uuid.uuid4(),
        email="new@example.com",
        full_name="New User",
        avatar_url=None,
    )
    user = user_service.sync_user(db_session, claims)
    assert user.email == "new@example.com"
    assert db_session.scalar(select(User).where(User.id == user.id)) is not None


def test_create_organization_adds_owner_membership(db_session: Session):
    user = User(
        supabase_id=uuid.uuid4(),
        email="owner@example.com",
        full_name="Owner",
    )
    db_session.add(user)
    db_session.commit()

    org = user_service.create_organization(db_session, user, "Acme")
    membership = db_session.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
    )
    assert membership is not None
    assert membership.role == OrganizationRole.owner
    assert user.active_organization_id == org.id


def test_join_organization_with_invite_code(db_session: Session):
    owner = User(supabase_id=uuid.uuid4(), email="owner@example.com", full_name="Owner")
    joiner = User(supabase_id=uuid.uuid4(), email="joiner@example.com", full_name="Joiner")
    db_session.add_all([owner, joiner])
    db_session.commit()

    org = user_service.create_organization(db_session, owner, "Acme")
    invite = user_service.create_invite(
        db_session,
        owner,
        org.id,
        OrganizationRole.member,
        None,
        None,
    )

    joined = user_service.join_organization(db_session, joiner, invite.code)
    assert joined.id == org.id
    membership = user_service.get_membership(db_session, joiner.id, org.id)
    assert membership is not None
    assert membership.role == OrganizationRole.member


def test_join_organization_rejects_revoked_invite(db_session: Session):
    owner = User(supabase_id=uuid.uuid4(), email="owner@example.com", full_name="Owner")
    joiner = User(supabase_id=uuid.uuid4(), email="joiner@example.com", full_name="Joiner")
    db_session.add_all([owner, joiner])
    db_session.commit()

    org = user_service.create_organization(db_session, owner, "Acme")
    invite = user_service.create_invite(
        db_session,
        owner,
        org.id,
        OrganizationRole.member,
        None,
        None,
    )
    user_service.revoke_invite(db_session, owner, org.id, invite.id)

    with pytest.raises(ValidationError):
        user_service.join_organization(db_session, joiner, invite.code)
