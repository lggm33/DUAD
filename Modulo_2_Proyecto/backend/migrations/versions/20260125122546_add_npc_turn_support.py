"""add npc turn support

Revision ID: 20260125122546
Revises: 008b2b82d1e9
Create Date: 2026-01-25 12:25:46.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260125122546'
down_revision: Union[str, None] = '008b2b82d1e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add NPC turn support to games table."""
    
    # Add current_turn_type column
    op.add_column(
        'games',
        sa.Column(
            'current_turn_type',
            sa.String(length=10),
            nullable=True
        )
    )
    
    # Add current_turn_npc_id column
    op.add_column(
        'games',
        sa.Column(
            'current_turn_npc_id',
            sa.Integer(),
            nullable=True
        )
    )
    
    # Add foreign key constraint for NPC
    op.create_foreign_key(
        'fk_games_current_turn_npc_id',
        'games',
        'npcs',
        ['current_turn_npc_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add index for performance
    op.create_index(
        'ix_games_current_turn_npc_id',
        'games',
        ['current_turn_npc_id'],
        unique=False
    )
    
    # Migrate existing data: if current_turn_user_id IS NOT NULL, set current_turn_type = 'USER'
    op.execute(
        """
        UPDATE games
        SET current_turn_type = 'USER'
        WHERE current_turn_user_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Remove NPC turn support from games table."""
    
    # Drop index
    op.drop_index('ix_games_current_turn_npc_id', table_name='games')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_games_current_turn_npc_id', 'games', type_='foreignkey')
    
    # Drop columns
    op.drop_column('games', 'current_turn_npc_id')
    op.drop_column('games', 'current_turn_type')
