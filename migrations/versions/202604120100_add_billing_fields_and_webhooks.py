"""
Revision ID: 202604120100
Revises: 202604120001
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa


revision = "202604120100"
down_revision = "202604120001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("stripe_customer_id", sa.String(length=64), nullable=True))
    op.add_column("user", sa.Column("stripe_subscription_id", sa.String(length=64), nullable=True))
    op.add_column("user", sa.Column("plan_code", sa.String(length=32), nullable=True))
    op.add_column("user", sa.Column("subscription_status", sa.String(length=32), nullable=True))
    op.add_column("user", sa.Column("subscription_period_end", sa.DateTime(), nullable=True))
    op.create_index("ix_user_stripe_customer_id", "user", ["stripe_customer_id"], unique=False)
    op.create_index("ix_user_stripe_subscription_id", "user", ["stripe_subscription_id"], unique=False)
    op.create_index("ix_user_plan_code", "user", ["plan_code"], unique=False)

    op.create_table(
        "processed_webhook_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(
        "ix_processed_webhook_event_event_id",
        "processed_webhook_event",
        ["event_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_processed_webhook_event_event_id", table_name="processed_webhook_event")
    op.drop_table("processed_webhook_event")

    op.drop_index("ix_user_plan_code", table_name="user")
    op.drop_index("ix_user_stripe_subscription_id", table_name="user")
    op.drop_index("ix_user_stripe_customer_id", table_name="user")
    op.drop_column("user", "subscription_period_end")
    op.drop_column("user", "subscription_status")
    op.drop_column("user", "plan_code")
    op.drop_column("user", "stripe_subscription_id")
    op.drop_column("user", "stripe_customer_id")
