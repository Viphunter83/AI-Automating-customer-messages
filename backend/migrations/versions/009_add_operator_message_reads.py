"""Add operator_message_reads table for tracking unread messages

Revision ID: 009
Revises: 008
Create Date: 2025-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_operator_message_reads'
down_revision = '008_add_failed_attempts_to_reminders'
branch_labels = None
depends_on = None


def upgrade():
    # Create operator_message_reads table
    op.create_table(
        'operator_message_reads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('operator_id', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('last_read_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_read_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['last_read_message_id'], ['messages.id'], ),
        sa.UniqueConstraint('operator_id', 'client_id', name='uq_operator_client_read'),
        comment='Tracks which messages operators have read for unread indicators'
    )
    
    # Create indexes
    op.create_index('ix_operator_message_reads_operator_id', 'operator_message_reads', ['operator_id'])
    op.create_index('ix_operator_message_reads_client_id', 'operator_message_reads', ['client_id'])
    op.create_index('ix_operator_message_reads_last_read_at', 'operator_message_reads', ['last_read_at'])


def downgrade():
    op.drop_index('ix_operator_message_reads_last_read_at', table_name='operator_message_reads')
    op.drop_index('ix_operator_message_reads_client_id', table_name='operator_message_reads')
    op.drop_index('ix_operator_message_reads_operator_id', table_name='operator_message_reads')
    op.drop_table('operator_message_reads')

