"""Add failed_attempts to reminders

Revision ID: 008_add_failed_attempts_to_reminders
Revises: 007_add_webhook_to_chatsession
Create Date: 2025-12-01 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_add_failed_attempts_to_reminders'
down_revision = '007_add_webhook_to_chatsession'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add failed_attempts and last_failed_at to reminders table
    op.add_column('reminders', sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('reminders', sa.Column('last_failed_at', sa.DateTime(), nullable=True))
    op.add_column('reminders', sa.Column('max_retry_attempts', sa.Integer(), nullable=False, server_default='3'))


def downgrade() -> None:
    op.drop_column('reminders', 'max_retry_attempts')
    op.drop_column('reminders', 'last_failed_at')
    op.drop_column('reminders', 'failed_attempts')

