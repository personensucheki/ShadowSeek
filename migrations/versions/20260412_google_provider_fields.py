"""
Add provider fields to LiveStream
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260412_google_provider_fields'
down_revision = "a184225fa484"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('live_stream', sa.Column('provider', sa.String(length=32), nullable=True))
    op.add_column('live_stream', sa.Column('provider_input_id', sa.String(length=128), nullable=True))
    op.add_column('live_stream', sa.Column('provider_channel_id', sa.String(length=128), nullable=True))
    op.add_column('live_stream', sa.Column('ingest_url', sa.String(length=512), nullable=True))
    op.add_column('live_stream', sa.Column('playback_url', sa.String(length=512), nullable=True))
    op.add_column('live_stream', sa.Column('provider_status', sa.Enum('draft', 'provisioning', 'ready', 'live', 'ended', 'error', name='live_stream_status'), nullable=False, server_default='draft'))
    op.add_column('live_stream', sa.Column('provider_output_bucket', sa.String(length=128), nullable=True))
    op.add_column('live_stream', sa.Column('location', sa.String(length=64), nullable=True))
    op.add_column('live_stream', sa.Column('stream_key', sa.String(length=128), nullable=True))

def downgrade():
    op.drop_column('live_stream', 'provider')
    op.drop_column('live_stream', 'provider_input_id')
    op.drop_column('live_stream', 'provider_channel_id')
    op.drop_column('live_stream', 'ingest_url')
    op.drop_column('live_stream', 'playback_url')
    op.drop_column('live_stream', 'provider_status')
    op.drop_column('live_stream', 'provider_output_bucket')
    op.drop_column('live_stream', 'location')
    op.drop_column('live_stream', 'stream_key')
