"""Initial schema creation

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-26 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create ENUM types
    messageType = postgresql.ENUM('user', 'bot_auto', 'bot_escalated', 'operator', name='messagetype')
    messageType.create(op.get_bind(), checkfirst=True)
    
    scenarioType = postgresql.ENUM(
        'GREETING', 'REFERRAL', 'TECH_SUPPORT_BASIC', 'UNKNOWN',
        name='scenariotype'
    )
    scenarioType.create(op.get_bind(), checkfirst=True)

    # messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', messageType, nullable=False, server_default='user'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_messages_client_id', 'client_id')
    )

    # classifications table
    op.create_table(
        'classifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('detected_scenario', scenarioType, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('ai_model', sa.String(100), nullable=True, server_default='openai_4o_mini'),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_classifications_message_id', 'message_id')
    )

    # response_templates table
    op.create_table(
        'response_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_name', scenarioType, nullable=False),
        sa.Column('template_text', sa.Text(), nullable=False),
        sa.Column('requires_params', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_name')
    )

    # keywords table
    op.create_table(
        'keywords',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_name', scenarioType, nullable=False),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_keywords_scenario_name', 'scenario_name')
    )

    # operator_feedback table
    op.create_table(
        'operator_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('classification_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operator_id', sa.String(255), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('suggested_scenario', scenarioType, nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['classification_id'], ['classifications.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_operator_feedback_message_id', 'message_id')
    )

    # operator_session_logs table
    op.create_table(
        'operator_session_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('bot_interaction_history', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('escalated_at', sa.DateTime(), nullable=True),
        sa.Column('operator_id', sa.String(255), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_operator_session_logs_client_id', 'client_id')
    )

def downgrade() -> None:
    op.drop_index('ix_operator_session_logs_client_id', table_name='operator_session_logs')
    op.drop_table('operator_session_logs')
    op.drop_index('ix_operator_feedback_message_id', table_name='operator_feedback')
    op.drop_table('operator_feedback')
    op.drop_index('ix_keywords_scenario_name', table_name='keywords')
    op.drop_table('keywords')
    op.drop_table('response_templates')
    op.drop_index('ix_classifications_message_id', table_name='classifications')
    op.drop_table('classifications')
    op.drop_index('ix_messages_client_id', table_name='messages')
    op.drop_table('messages')
    
    # Drop ENUM types
    sa.Enum(name='scenariotype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='messagetype').drop(op.get_bind(), checkfirst=True)

