"""Create npcs table

Revision ID: d71244959f3e
Revises: f0a1b2c3d4e5
Create Date: 2025-12-31 21:30:35.754946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd71244959f3e'
down_revision: Union[str, Sequence[str], None] = 'f0a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create npcs table
    op.create_table('npcs',
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('npc_type', sa.Enum('ALLY', 'ENEMY', 'NEUTRAL', 'BOSS', 'COMPANION', name='npc_type', create_type=True), server_default=sa.text("'NEUTRAL'"), nullable=False),
    sa.Column('status', sa.Enum('ACTIVE', 'DEFEATED', 'RETIRED', 'CONVERTED_TO_PC', name='npc_status', create_type=True), server_default=sa.text("'ACTIVE'"), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('stats', sa.JSON(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('converted_from_character_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['converted_from_character_id'], ['characters.id'], name=op.f('fk_npcs_converted_from_character_id_characters'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name=op.f('fk_npcs_game_id_games'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_npcs'))
    )
    op.create_index(op.f('ix_npcs_game_id'), 'npcs', ['game_id'], unique=False)

    # Add FK from characters.converted_to_npc_id to npcs.id
    op.create_foreign_key(
        op.f('fk_characters_converted_to_npc_id_npcs'),
        'characters', 'npcs',
        ['converted_to_npc_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop FK from characters to npcs
    op.drop_constraint(op.f('fk_characters_converted_to_npc_id_npcs'), 'characters', type_='foreignkey')

    # Drop npcs table
    op.drop_index(op.f('ix_npcs_game_id'), table_name='npcs')
    op.drop_table('npcs')

    # Drop enum types
    sa.Enum(name='npc_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='npc_status').drop(op.get_bind(), checkfirst=True)
