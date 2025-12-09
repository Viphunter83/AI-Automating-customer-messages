"""Add new scenario types: LESSON_LINK, LESSON_CANCELLATION, GREETING_TIME_REQUEST

Revision ID: 010_add_new_scenarios
Revises: 009_add_operator_message_reads
Create Date: 2025-12-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_new_scenarios'
down_revision = '009_add_operator_message_reads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values to ScenarioType
    # PostgreSQL requires these to be added one at a time in separate transactions
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'LESSON_LINK'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'LESSON_CANCELLATION'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'GREETING_TIME_REQUEST'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # In production, this should be handled carefully
    pass







