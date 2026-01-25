"""Add character_name to chat_messages

Revision ID: 69a5d44b8ba0
Revises: f1a2b3c4d5e6
Create Date: 2026-01-05 19:49:16.805696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69a5d44b8ba0'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add character_name column to chat_messages table
    op.add_column('chat_messages', sa.Column('character_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove character_name column from chat_messages table
    op.drop_column('chat_messages', 'character_name')
