"""Create characters table

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2024-12-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, None] = 'e9f0a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create character_status enum (checkfirst=True to avoid error if exists)
    character_status_enum = sa.Enum(
        'DRAFT',
        'PENDING_APPROVAL',
        'APPROVED',
        'REJECTED',
        'CONVERTED_TO_NPC',
        name='character_status'
    )
    character_status_enum.create(op.get_bind(), checkfirst=True)

    # Create characters table using postgresql.ENUM to avoid auto-creation
    from sqlalchemy.dialects import postgresql
    status_enum = postgresql.ENUM(
        'DRAFT',
        'PENDING_APPROVAL',
        'APPROVED',
        'REJECTED',
        'CONVERTED_TO_NPC',
        name='character_status',
        create_type=False  # Don't try to create, we already did
    )

    op.create_table(
        'characters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column(
            'status',
            status_enum,
            nullable=False,
            server_default=sa.text("'DRAFT'")
        ),
        sa.Column('data', sa.JSON(), nullable=False, default={}),
        sa.Column('dm_feedback', sa.Text(), nullable=True),
        sa.Column('converted_to_npc_id', sa.Integer(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['game_id'],
            ['games.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),
        # Note: converted_to_npc_id FK will be added when npcs table exists
    )

    # Create indexes
    op.create_index('ix_characters_game_id', 'characters', ['game_id'])
    op.create_index('ix_characters_user_id', 'characters', ['user_id'])

    # Unique constraint: one character per user per game
    op.create_unique_constraint(
        'uq_characters_game_user',
        'characters',
        ['game_id', 'user_id']
    )


def downgrade() -> None:
    # Drop table and indexes
    op.drop_constraint('uq_characters_game_user', 'characters', type_='unique')
    op.drop_index('ix_characters_user_id', 'characters')
    op.drop_index('ix_characters_game_id', 'characters')
    op.drop_table('characters')

    # Drop enum type
    sa.Enum(name='character_status').drop(op.get_bind(), checkfirst=True)

