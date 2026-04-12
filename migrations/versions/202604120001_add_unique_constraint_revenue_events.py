"""add unique constraint to revenue_events (platform, username, captured_at, source)

Revision ID: 202604120001
Revises: a987932bf3d9
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '202604120001'
down_revision = 'a987932bf3d9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("revenue_events", schema=None) as batch_op:
        conn = op.get_bind()
        if conn.dialect.name != 'sqlite':
            batch_op.create_unique_constraint(
                "uq_revenue_event",
                ["platform", "username", "captured_at", "source"]
            )


def downgrade():
    with op.batch_alter_table("revenue_events", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_revenue_event",
            type_="unique"
        )
