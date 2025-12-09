"""Add webhook fields to chat_sessions

Revision ID: 007_add_webhook_to_chatsession
Revises: 006_add_performance_indexes
Create Date: 2025-12-01 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_webhook_to_chatsession'
down_revision = '006_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add webhook-related fields to chat_sessions table
    op.add_column('chat_sessions', sa.Column('webhook_url', sa.String(500), nullable=True))
    op.add_column('chat_sessions', sa.Column('platform', sa.String(50), nullable=True))
    op.add_column('chat_sessions', sa.Column('chat_id', sa.String(255), nullable=True))
    
    # Add index on platform for faster lookups
    op.create_index('ix_chat_sessions_platform', 'chat_sessions', ['platform'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_chat_sessions_platform', table_name='chat_sessions')
    op.drop_column('chat_sessions', 'chat_id')
    op.drop_column('chat_sessions', 'platform')
    op.drop_column('chat_sessions', 'webhook_url')










