"""Add chat_sessions table

Revision ID: 004_add_chat_sessions
Revises: 003_add_reminders
Create Date: 2025-11-26 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_chat_sessions'
down_revision = '003_add_reminders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create DialogStatus ENUM
    dialogStatus = postgresql.ENUM('open', 'closed', 'escalated', name='dialogstatus')
    dialogStatus.create(op.get_bind(), checkfirst=True)

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('status', dialogStatus, nullable=False, server_default='open'),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('farewell_sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_chat_sessions_client_id', 'chat_sessions', ['client_id'], unique=True)
    op.create_index('ix_chat_sessions_status', 'chat_sessions', ['status'], unique=False)
    op.create_index('ix_chat_sessions_last_activity_at', 'chat_sessions', ['last_activity_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_chat_sessions_last_activity_at', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_status', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_client_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')
    postgresql.ENUM(name='dialogstatus').drop(op.get_bind(), checkfirst=True)










