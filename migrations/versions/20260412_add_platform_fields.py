"""
Add multi-platform fields to PublicProfile and RevenueEvent
"""
from alembic import op
import sqlalchemy as sa


revision = "202604120550"
down_revision = "ff0e989c5f5b"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _column_names(inspector, table_name):
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    profile_columns = {
        "follower_count": sa.Column("follower_count", sa.Integer(), nullable=True),
        "engagement": sa.Column("engagement", sa.Float(), nullable=True),
        "tags": sa.Column("tags", sa.String(length=255), nullable=True),
        "ranking_position": sa.Column("ranking_position", sa.Integer(), nullable=True),
        "source_url": sa.Column("source_url", sa.String(length=255), nullable=True),
    }
    if _table_exists(inspector, "public_profile"):
        existing_profile_columns = _column_names(inspector, "public_profile")
        with op.batch_alter_table("public_profile") as batch_op:
            for column_name, column in profile_columns.items():
                if column_name not in existing_profile_columns:
                    batch_op.add_column(column)

    revenue_columns = {
        "viewer_count": sa.Column("viewer_count", sa.Integer(), nullable=True),
        "engagement": sa.Column("engagement", sa.Float(), nullable=True),
        "ranking_position": sa.Column("ranking_position", sa.Integer(), nullable=True),
        "source_url": sa.Column("source_url", sa.String(length=255), nullable=True),
    }
    if not _table_exists(inspector, "revenue_events"):
        op.create_table(
            "revenue_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("platform", sa.String(length=32), nullable=False),
            sa.Column("username", sa.String(length=64), nullable=False),
            sa.Column("display_name", sa.String(length=128), nullable=True),
            sa.Column("estimated_revenue", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=8), nullable=False),
            sa.Column("diamonds", sa.Integer(), nullable=True),
            sa.Column("followers", sa.Integer(), nullable=True),
            sa.Column("viewer_count", sa.Integer(), nullable=True),
            sa.Column("engagement", sa.Float(), nullable=True),
            sa.Column("ranking_position", sa.Integer(), nullable=True),
            sa.Column("source_url", sa.String(length=255), nullable=True),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("confidence", sa.String(length=16), nullable=True),
            sa.Column("captured_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        existing_revenue_columns = _column_names(inspector, "revenue_events")
        with op.batch_alter_table("revenue_events") as batch_op:
            for column_name, column in revenue_columns.items():
                if column_name not in existing_revenue_columns:
                    batch_op.add_column(column)

def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "public_profile"):
        existing_profile_columns = _column_names(inspector, "public_profile")
        with op.batch_alter_table("public_profile") as batch_op:
            for column_name in ("follower_count", "engagement", "tags", "ranking_position", "source_url"):
                if column_name in existing_profile_columns:
                    batch_op.drop_column(column_name)

    if _table_exists(inspector, "revenue_events"):
        existing_revenue_columns = _column_names(inspector, "revenue_events")
        with op.batch_alter_table("revenue_events") as batch_op:
            for column_name in ("viewer_count", "engagement", "ranking_position", "source_url"):
                if column_name in existing_revenue_columns:
                    batch_op.drop_column(column_name)
