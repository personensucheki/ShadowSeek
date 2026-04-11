"""
Revision ID: 202604111200
Revises: 
Create Date: 2026-04-11
"""
revision = '202604111200'
down_revision = '7a3e1d1cf1ce'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('user', sa.Column('display_name', sa.String(length=80), nullable=True))
    op.add_column('user', sa.Column('bio', sa.String(length=500), nullable=True))

def downgrade():
    op.drop_column('user', 'display_name')
    op.drop_column('user', 'bio')
