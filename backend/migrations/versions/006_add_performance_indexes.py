"""Add performance indexes and constraints

Revision ID: 006_add_performance_indexes
Revises: 005_add_message_priorities
Create Date: 2025-11-26 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_performance_indexes'
down_revision = '005_add_message_priorities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============ MESSAGES TABLE INDEXES ============
    
    # Index on created_at for time-based queries
    op.create_index(
        'ix_messages_created_at',
        'messages',
        ['created_at'],
        unique=False
    )
    
    # Composite index for client messages ordered by time
    op.create_index(
        'ix_messages_client_created',
        'messages',
        ['client_id', 'created_at'],
        unique=False
    )
    
    # Composite index for priority and created_at (for escalation queue)
    op.create_index(
        'ix_messages_priority_created',
        'messages',
        ['priority', 'created_at'],
        unique=False
    )
    
    # Index on is_processed for filtering unprocessed messages
    op.create_index(
        'ix_messages_is_processed',
        'messages',
        ['is_processed'],
        unique=False
    )
    
    # ============ CLASSIFICATIONS TABLE INDEXES ============
    
    # Composite index for message classification queries
    op.create_index(
        'ix_classifications_message_created',
        'classifications',
        ['message_id', 'created_at'],
        unique=False
    )
    
    # Index on detected_scenario for analytics
    op.create_index(
        'ix_classifications_scenario',
        'classifications',
        ['detected_scenario'],
        unique=False
    )
    
    # ============ REMINDERS TABLE INDEXES ============
    
    # Composite index for finding pending reminders by client
    op.create_index(
        'ix_reminders_client_scheduled_cancelled',
        'reminders',
        ['client_id', 'scheduled_at', 'is_cancelled'],
        unique=False
    )
    
    # Composite index for reminder scheduler queries
    op.create_index(
        'ix_reminders_scheduled_cancelled_sent',
        'reminders',
        ['scheduled_at', 'is_cancelled', 'sent_at'],
        unique=False
    )
    
    # ============ CHAT_SESSIONS TABLE INDEXES ============
    
    # Composite index for finding sessions by status and activity
    op.create_index(
        'ix_chat_sessions_status_activity',
        'chat_sessions',
        ['status', 'last_activity_at'],
        unique=False
    )
    
    # ============ FOREIGN KEY CONSTRAINTS ============
    
    # Ensure message_id in classifications references messages
    # (SQLAlchemy should have created this, but we ensure it exists)
    try:
        op.create_foreign_key(
            'fk_classifications_message_id',
            'classifications',
            'messages',
            ['message_id'],
            ['id'],
            ondelete='CASCADE'
        )
    except Exception:
        # Foreign key might already exist
        pass
    
    # Ensure message_id in reminders references messages
    try:
        op.create_foreign_key(
            'fk_reminders_message_id',
            'reminders',
            'messages',
            ['message_id'],
            ['id'],
            ondelete='CASCADE'
        )
    except Exception:
        # Foreign key might already exist
        pass
    
    # Ensure message_id in operator_feedback references messages
    try:
        op.create_foreign_key(
            'fk_operator_feedback_message_id',
            'operator_feedback',
            'messages',
            ['message_id'],
            ['id'],
            ondelete='CASCADE'
        )
    except Exception:
        # Foreign key might already exist
        pass
    
    # Ensure classification_id in operator_feedback references classifications
    try:
        op.create_foreign_key(
            'fk_operator_feedback_classification_id',
            'operator_feedback',
            'classifications',
            ['classification_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # Foreign key might already exist
        pass
    
    # ============ CHECK CONSTRAINTS ============
    
    # Check constraint for confidence (0-1)
    try:
        op.create_check_constraint(
            'ck_classifications_confidence_range',
            'classifications',
            sa.text('confidence >= 0 AND confidence <= 1')
        )
    except Exception:
        pass
    
    # ============ UNIQUE CONSTRAINTS ============
    
    # One active template per scenario (partial unique index)
    # Note: PostgreSQL partial unique index syntax
    try:
        # Create partial unique index instead of constraint (better for conditional uniqueness)
        op.execute(sa.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_response_templates_scenario_active 
            ON response_templates (scenario_name) 
            WHERE is_active = true
        """))
    except Exception:
        pass


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_chat_sessions_status_activity', table_name='chat_sessions')
    op.drop_index('ix_reminders_scheduled_cancelled_sent', table_name='reminders')
    op.drop_index('ix_reminders_client_scheduled_cancelled', table_name='reminders')
    op.drop_index('ix_classifications_scenario', table_name='classifications')
    op.drop_index('ix_classifications_message_created', table_name='classifications')
    op.drop_index('ix_messages_is_processed', table_name='messages')
    op.drop_index('ix_messages_priority_created', table_name='messages')
    op.drop_index('ix_messages_client_created', table_name='messages')
    op.drop_index('ix_messages_created_at', table_name='messages')
    
    # Drop foreign keys (if they were created by this migration)
    try:
        op.drop_constraint('fk_operator_feedback_classification_id', 'operator_feedback', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_constraint('fk_operator_feedback_message_id', 'operator_feedback', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_constraint('fk_reminders_message_id', 'reminders', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.drop_constraint('fk_classifications_message_id', 'classifications', type_='foreignkey')
    except Exception:
        pass

