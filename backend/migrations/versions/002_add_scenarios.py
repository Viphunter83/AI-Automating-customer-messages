"""Add new scenario types

Revision ID: 002_add_scenarios
Revises: 001_initial_schema
Create Date: 2025-11-26 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_scenarios'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values to ScenarioType
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'FAREWELL'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'REMINDER'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'ABSENCE_REQUEST'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'SCHEDULE_CHANGE'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'COMPLAINT'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'MISSING_TRAINER'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'MASS_OUTAGE'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'REVIEW_BONUS'")
    op.execute("ALTER TYPE scenariotype ADD VALUE IF NOT EXISTS 'CROSS_EXTENSION'")
    
    # Add is_first_message column to messages table
    op.add_column('messages', sa.Column('is_first_message', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_first_message column
    op.drop_column('messages', 'is_first_message')
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # In production, this should be handled carefully
    pass

