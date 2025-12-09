"""Add reminders table

Revision ID: 003_add_reminders
Revises: 002_add_scenarios
Create Date: 2025-11-26 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_reminders'
down_revision = '002_add_scenarios'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ReminderType enum
    reminderType = postgresql.ENUM(
        'reminder_15min', 'reminder_30min', 'reminder_1day',
        name='remindertype'
    )
    reminderType.create(op.get_bind(), checkfirst=True)
    
    # Create reminders table
    op.create_table(
        'reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reminder_type', reminderType, nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('is_cancelled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_reminders_client_id', 'client_id'),
        sa.Index('ix_reminders_message_id', 'message_id'),
        sa.Index('ix_reminders_scheduled_at', 'scheduled_at')
    )


def downgrade() -> None:
    op.drop_index('ix_reminders_scheduled_at', table_name='reminders')
    op.drop_index('ix_reminders_message_id', table_name='reminders')
    op.drop_index('ix_reminders_client_id', table_name='reminders')
    op.drop_table('reminders')
    sa.Enum(name='remindertype').drop(op.get_bind(), checkfirst=True)










