"""add missing columns to media_posts

Revision ID: 20260412_9998
Revises: 20260412_9999
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260412_9998'
down_revision = '20260412_9999'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('media_posts') as batch_op:
        batch_op.add_column(sa.Column('hashtags', sa.String(length=400), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('trim_start', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('trim_end', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('media_posts') as batch_op:
        batch_op.drop_column('trim_end')
        batch_op.drop_column('trim_start')
        batch_op.drop_column('location')
        batch_op.drop_column('hashtags')
