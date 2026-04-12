"""
add community features

Revision ID: 202604120600
Revises: ff0e989c5f5b
Create Date: 2026-04-12 06:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202604120600"
down_revision = "ff0e989c5f5b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("country", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("city", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("last_seen_at", sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f("ix_user_country"), ["country"], unique=False)
        batch_op.create_index(batch_op.f("ix_user_last_seen_at"), ["last_seen_at"], unique=False)

    op.create_table(
        "direct_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["recipient_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("direct_messages", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_direct_messages_sender_id"), ["sender_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_direct_messages_recipient_id"), ["recipient_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_direct_messages_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_direct_messages_read_at"), ["read_at"], unique=False)


def downgrade():
    with op.batch_alter_table("direct_messages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_direct_messages_read_at"))
        batch_op.drop_index(batch_op.f("ix_direct_messages_created_at"))
        batch_op.drop_index(batch_op.f("ix_direct_messages_recipient_id"))
        batch_op.drop_index(batch_op.f("ix_direct_messages_sender_id"))

    op.drop_table("direct_messages")

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_last_seen_at"))
        batch_op.drop_index(batch_op.f("ix_user_country"))
        batch_op.drop_column("last_seen_at")
        batch_op.drop_column("city")
        batch_op.drop_column("country")
