"""
add community features

Revision ID: 202604120600
Revises: 202604120550
Create Date: 2026-04-12 06:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "202604120600"
down_revision = "202604120550"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _column_names(inspector, table_name):
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector, table_name):
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {
        "country": sa.Column("country", sa.String(length=80), nullable=True),
        "city": sa.Column("city", sa.String(length=120), nullable=True),
        "last_seen_at": sa.Column("last_seen_at", sa.DateTime(), nullable=True),
    }
    existing_user_columns = _column_names(inspector, "user")
    existing_user_indexes = _index_names(inspector, "user")
    with op.batch_alter_table("user", schema=None) as batch_op:
        for column_name, column in user_columns.items():
            if column_name not in existing_user_columns:
                batch_op.add_column(column)
        if "ix_user_country" not in existing_user_indexes:
            batch_op.create_index(batch_op.f("ix_user_country"), ["country"], unique=False)
        if "ix_user_last_seen_at" not in existing_user_indexes:
            batch_op.create_index(batch_op.f("ix_user_last_seen_at"), ["last_seen_at"], unique=False)

    if not _table_exists(inspector, "direct_messages"):
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

    inspector = sa.inspect(bind)
    existing_dm_indexes = _index_names(inspector, "direct_messages")
    with op.batch_alter_table("direct_messages", schema=None) as batch_op:
        if "ix_direct_messages_sender_id" not in existing_dm_indexes:
            batch_op.create_index(batch_op.f("ix_direct_messages_sender_id"), ["sender_id"], unique=False)
        if "ix_direct_messages_recipient_id" not in existing_dm_indexes:
            batch_op.create_index(batch_op.f("ix_direct_messages_recipient_id"), ["recipient_id"], unique=False)
        if "ix_direct_messages_created_at" not in existing_dm_indexes:
            batch_op.create_index(batch_op.f("ix_direct_messages_created_at"), ["created_at"], unique=False)
        if "ix_direct_messages_read_at" not in existing_dm_indexes:
            batch_op.create_index(batch_op.f("ix_direct_messages_read_at"), ["read_at"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "direct_messages"):
        existing_dm_indexes = _index_names(inspector, "direct_messages")
        with op.batch_alter_table("direct_messages", schema=None) as batch_op:
            if "ix_direct_messages_read_at" in existing_dm_indexes:
                batch_op.drop_index(batch_op.f("ix_direct_messages_read_at"))
            if "ix_direct_messages_created_at" in existing_dm_indexes:
                batch_op.drop_index(batch_op.f("ix_direct_messages_created_at"))
            if "ix_direct_messages_recipient_id" in existing_dm_indexes:
                batch_op.drop_index(batch_op.f("ix_direct_messages_recipient_id"))
            if "ix_direct_messages_sender_id" in existing_dm_indexes:
                batch_op.drop_index(batch_op.f("ix_direct_messages_sender_id"))
        op.drop_table("direct_messages")

    existing_user_indexes = _index_names(inspector, "user")
    existing_user_columns = _column_names(inspector, "user")
    with op.batch_alter_table("user", schema=None) as batch_op:
        if "ix_user_last_seen_at" in existing_user_indexes:
            batch_op.drop_index(batch_op.f("ix_user_last_seen_at"))
        if "ix_user_country" in existing_user_indexes:
            batch_op.drop_index(batch_op.f("ix_user_country"))
        if "last_seen_at" in existing_user_columns:
            batch_op.drop_column("last_seen_at")
        if "city" in existing_user_columns:
            batch_op.drop_column("city")
        if "country" in existing_user_columns:
            batch_op.drop_column("country")
