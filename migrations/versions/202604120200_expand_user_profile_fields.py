"""
Revision ID: 202604120200
Revises: 202604120100
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa


revision = "202604120200"
down_revision = "202604120100"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("profile_title", sa.String(length=120), nullable=True))
    op.add_column("user", sa.Column("birthdate", sa.Date(), nullable=True))
    op.add_column("user", sa.Column("gender", sa.String(length=32), nullable=True))
    op.add_column("user", sa.Column("height_cm", sa.Integer(), nullable=True))
    op.add_column("user", sa.Column("hobbies", sa.String(length=1000), nullable=True))
    op.add_column("user", sa.Column("interests", sa.String(length=1000), nullable=True))
    op.add_column("user", sa.Column("preferences", sa.String(length=1000), nullable=True))
    op.add_column("user", sa.Column("social_accounts", sa.Text(), nullable=True))
    op.add_column("user", sa.Column("support_contact", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("donation_link", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("banner", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("user", "banner")
    op.drop_column("user", "donation_link")
    op.drop_column("user", "support_contact")
    op.drop_column("user", "social_accounts")
    op.drop_column("user", "preferences")
    op.drop_column("user", "interests")
    op.drop_column("user", "hobbies")
    op.drop_column("user", "height_cm")
    op.drop_column("user", "gender")
    op.drop_column("user", "birthdate")
    op.drop_column("user", "profile_title")
