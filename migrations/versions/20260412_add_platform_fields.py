"""
Add multi-platform fields to PublicProfile and RevenueEvent
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    with op.batch_alter_table('public_profile') as batch_op:
        batch_op.add_column(sa.Column('follower_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('engagement', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('tags', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('ranking_position', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('source_url', sa.String(length=255), nullable=True))
    with op.batch_alter_table('revenue_events') as batch_op:
        batch_op.add_column(sa.Column('viewer_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('engagement', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('ranking_position', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('source_url', sa.String(length=255), nullable=True))

def downgrade():
    with op.batch_alter_table('public_profile') as batch_op:
        batch_op.drop_column('follower_count')
        batch_op.drop_column('engagement')
        batch_op.drop_column('tags')
        batch_op.drop_column('ranking_position')
        batch_op.drop_column('source_url')
    with op.batch_alter_table('revenue_events') as batch_op:
        batch_op.drop_column('viewer_count')
        batch_op.drop_column('engagement')
        batch_op.drop_column('ranking_position')
        batch_op.drop_column('source_url')
