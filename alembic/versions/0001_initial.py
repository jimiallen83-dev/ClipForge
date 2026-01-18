"""Initial schema migration

Revision ID: 0001_initial
Revises: None
Create Date: 2026-01-15
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("channel_id", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("credentials", sa.Text(), nullable=True),
    )

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("privacy", sa.String(), nullable=True),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True, index=True),
    )

    op.create_table(
        "clips",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=True, index=True),
        sa.Column("clip_id", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("start", sa.Float(), nullable=True),
        sa.Column("end", sa.Float(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True, default=0.0),
        sa.Column("emotion", sa.String(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("approved", sa.String(), nullable=True, server_default="pending"),
        sa.Column(
            "renderer_status", sa.String(), nullable=True, server_default="not_rendered"
        ),
        sa.Column("output_path", sa.String(), nullable=True),
        sa.Column("thumbnail_path", sa.String(), nullable=True),
        sa.Column("title_suggestions", sa.Text(), nullable=True),
        sa.Column("script", sa.Text(), nullable=True),
        sa.Column("tts_path", sa.String(), nullable=True),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.String(), nullable=True, index=True),
        sa.Column("status", sa.String(), nullable=True, server_default="queued"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(), nullable=True, unique=True, index=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("tier", sa.String(), nullable=True, server_default="free"),
        sa.Column("api_key", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("tier", sa.String(), nullable=True),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("active", sa.String(), nullable=True, server_default="true"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("clip_id", sa.String(), nullable=True, index=True),
        sa.Column("event_type", sa.String(), nullable=True, index=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("events")
    op.drop_table("subscriptions")
    op.drop_table("users")
    op.drop_table("jobs")
    op.drop_table("clips")
    op.drop_table("projects")
    op.drop_table("videos")
    op.drop_table("channels")
