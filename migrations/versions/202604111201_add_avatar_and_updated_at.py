"""
Revision ID: 202604111201
Revises: 202604111200
Create Date: 2026-04-11
"""
revision = '202604111201'
down_revision = '202604111200'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('user', sa.Column('avatar', sa.String(length=255), nullable=True))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Set updated_at for existing users
    op.execute("UPDATE user SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")

def downgrade():
    op.drop_column('user', 'avatar')
    op.drop_column('user', 'updated_at')
