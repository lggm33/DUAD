"""add turn tracking to games

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-01-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add turn tracking fields to games table."""
    # Add current_turn_user_id column
    op.add_column(
        'games',
        sa.Column(
            'current_turn_user_id',
            sa.Integer(),
            nullable=True
        )
    )
    
    # Add current_turn_character_name column
    op.add_column(
        'games',
        sa.Column(
            'current_turn_character_name',
            sa.String(length=255),
            nullable=True
        )
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_games_current_turn_user_id',
        'games',
        'users',
        ['current_turn_user_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for performance
    op.create_index(
        'ix_games_current_turn_user_id',
        'games',
        ['current_turn_user_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove turn tracking fields from games table."""
    # Drop index
    op.drop_index('ix_games_current_turn_user_id', table_name='games')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_games_current_turn_user_id', 'games', type_='foreignkey')
    
    # Drop columns
    op.drop_column('games', 'current_turn_character_name')
    op.drop_column('games', 'current_turn_user_id')
