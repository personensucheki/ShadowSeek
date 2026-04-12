"""repair media_posts table if missing

Revision ID: 20260412_9999
Revises: 717508cd116c
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20260412_9999'
down_revision = '717508cd116c'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'media_posts' not in inspector.get_table_names():
        op.create_table(
            "media_posts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("media_type", sa.String(length=16), nullable=False),
            sa.Column("file_path", sa.String(length=255), nullable=False),
            sa.Column("caption", sa.String(length=500), nullable=True),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index("ix_media_posts_user_id", "media_posts", ["user_id"])
        op.create_index("ix_media_posts_created_at", "media_posts", ["created_at"])
        op.create_index("ix_media_posts_is_public", "media_posts", ["is_public"])
        op.create_index("ix_media_posts_media_type", "media_posts", ["media_type"])

def downgrade():
    op.drop_index("ix_media_posts_media_type", table_name="media_posts")
    op.drop_index("ix_media_posts_is_public", table_name="media_posts")
    op.drop_index("ix_media_posts_created_at", table_name="media_posts")
    op.drop_index("ix_media_posts_user_id", table_name="media_posts")
    op.drop_table("media_posts")
