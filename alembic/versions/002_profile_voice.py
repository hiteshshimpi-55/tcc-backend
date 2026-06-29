"""Add org profile, user personal profile, and voice profile tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002_profile_voice"
down_revision: str | None = "001_initial_auth_org"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

startup_role_type = postgresql.ENUM(
    "founder",
    "engineering",
    "product",
    "growth",
    "marketing",
    "customer_success",
    "operations",
    "people_hiring",
    name="startup_role",
    create_type=False,
)
writing_style_type = postgresql.ENUM(
    "concise",
    "detailed",
    "opinionated",
    name="writing_style",
    create_type=False,
)
emoji_usage_type = postgresql.ENUM(
    "none",
    "minimal",
    "expressive",
    name="emoji_usage",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE startup_role AS ENUM ("
        "'founder', 'engineering', 'product', 'growth', "
        "'marketing', 'customer_success', 'operations', 'people_hiring'"
        "); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE writing_style AS ENUM ('concise', 'detailed', 'opinionated'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE emoji_usage AS ENUM ('none', 'minimal', 'expressive'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    op.add_column("organizations", sa.Column("category", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("target_audience", sa.Text(), nullable=True))
    op.add_column(
        "organizations",
        sa.Column(
            "major_platforms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.add_column("users", sa.Column("role_title", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("startup_role", startup_role_type, nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "profile_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "user_voice_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("writing_style", writing_style_type, nullable=True),
        sa.Column("emoji_usage", emoji_usage_type, nullable=True),
        sa.Column(
            "preferred_tones",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("specialty_prompt", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_voice_profiles")
    op.drop_column("users", "profile_completed")
    op.drop_column("users", "startup_role")
    op.drop_column("users", "bio")
    op.drop_column("users", "role_title")
    op.drop_column("organizations", "major_platforms")
    op.drop_column("organizations", "target_audience")
    op.drop_column("organizations", "description")
    op.drop_column("organizations", "category")
    op.execute("DROP TYPE IF EXISTS emoji_usage")
    op.execute("DROP TYPE IF EXISTS writing_style")
    op.execute("DROP TYPE IF EXISTS startup_role")
