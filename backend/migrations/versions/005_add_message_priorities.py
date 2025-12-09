"""Add priority and escalation_reason to messages

Revision ID: 005_add_message_priorities
Revises: 004_add_chat_sessions
Create Date: 2025-11-26 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_message_priorities'
down_revision = '004_add_chat_sessions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PriorityLevel ENUM
    priority_level_type = postgresql.ENUM('low', 'medium', 'high', 'critical', name='prioritylevel')
    priority_level_type.create(op.get_bind(), checkfirst=True)
    
    # Create EscalationReason ENUM
    escalation_reason_type = postgresql.ENUM(
        'low_confidence',
        'repeated_failed',
        'complaint',
        'unknown_scenario',
        'operator_marked',
        'system_error',
        name='escalationreason'
    )
    escalation_reason_type.create(op.get_bind(), checkfirst=True)
    
    # Add priority column to messages table
    op.add_column('messages', sa.Column('priority', priority_level_type, nullable=False, server_default='low'))
    op.add_column('messages', sa.Column('escalation_reason', escalation_reason_type, nullable=True))
    op.add_column('messages', sa.Column('is_first_message', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create index on priority for faster sorting
    op.create_index('ix_messages_priority', 'messages', ['priority'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_messages_priority', table_name='messages')
    op.drop_column('messages', 'is_first_message')
    op.drop_column('messages', 'escalation_reason')
    op.drop_column('messages', 'priority')
    postgresql.ENUM(name='escalationreason').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='prioritylevel').drop(op.get_bind(), checkfirst=True)










