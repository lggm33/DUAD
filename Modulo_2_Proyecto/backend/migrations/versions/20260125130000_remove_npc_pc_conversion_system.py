"""remove_npc_pc_conversion_system

Revision ID: 20260125130000
Revises: 20260125122546
Create Date: 2026-01-25 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260125130000'
down_revision: Union[str, None] = '20260125122546'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove NPC-PC conversion system from database."""
    
    # 1. Update existing data to avoid enum value conflicts
    # NPCs with CONVERTED_TO_PC status become RETIRED
    op.execute(
        "UPDATE npcs SET status = 'RETIRED' WHERE status = 'CONVERTED_TO_PC'"
    )
    # Characters with CONVERTED_TO_NPC status become APPROVED
    op.execute(
        "UPDATE characters SET status = 'APPROVED' WHERE status = 'CONVERTED_TO_NPC'"
    )

    # 2. Drop Foreign Keys
    op.drop_constraint('fk_characters_converted_to_npc_id_npcs', 'characters', type_='foreignkey')
    op.drop_constraint('fk_npcs_converted_from_character_id_characters', 'npcs', type_='foreignkey')

    # 3. Drop Columns
    op.drop_column('characters', 'converted_to_npc_id')
    op.drop_column('npcs', 'converted_from_character_id')

    # 4. Handle Enums (PostgreSQL specific)
    # Since PostgreSQL doesn't support removing values from an enum type easily,
    # we leave the values in the database type for now to avoid complex migrations.
    # The application layer (Models) will no longer use them.


def downgrade() -> None:
    """Restore NPC-PC conversion system to database."""
    
    # Add columns back
    op.add_column('npcs', sa.Column('converted_from_character_id', sa.Integer(), nullable=True))
    op.add_column('characters', sa.Column('converted_to_npc_id', sa.Integer(), nullable=True))

    # Add constraints back
    op.create_foreign_key(
        'fk_npcs_converted_from_character_id_characters',
        'npcs', 'characters',
        ['converted_from_character_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_characters_converted_to_npc_id_npcs',
        'characters', 'npcs',
        ['converted_to_npc_id'], ['id'],
        ondelete='SET NULL'
    )
