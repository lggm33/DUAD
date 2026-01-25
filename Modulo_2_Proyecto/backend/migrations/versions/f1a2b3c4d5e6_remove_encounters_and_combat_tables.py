"""Remove encounters and combat tables

Revision ID: f1a2b3c4d5e6
Revises: f0a1b2c3d4e5
Create Date: 2026-01-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd71244959f3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Remove encounters and combat tables."""
    # Drop tables in reverse order (respecting FK dependencies)
    op.drop_index(op.f('ix_encounter_states_encounter_id'), table_name='encounter_states')
    op.drop_table('encounter_states')
    op.drop_index(op.f('ix_encounter_participants_encounter_id'), table_name='encounter_participants')
    op.drop_table('encounter_participants')
    op.drop_index(op.f('ix_combat_logs_encounter_id'), table_name='combat_logs')
    op.drop_table('combat_logs')
    op.drop_index(op.f('ix_encounters_game_id'), table_name='encounters')
    op.drop_table('encounters')

    # Drop enum types
    sa.Enum(name='encounter_state_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='participant_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='combat_action_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='actor_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='encounter_outcome').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='encounter_difficulty').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='encounter_status').drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema: Recreate encounters and combat tables."""
    # Recreate enum types
    sa.Enum('DRAFT', 'READY', 'ACTIVE', 'PAUSED', 'COMPLETED', name='encounter_status').create(op.get_bind(), checkfirst=True)
    sa.Enum('TRIVIAL', 'EASY', 'MEDIUM', 'HARD', 'DEADLY', name='encounter_difficulty').create(op.get_bind(), checkfirst=True)
    sa.Enum('VICTORY', 'DEFEAT', 'FLED', 'NEGOTIATED', 'ABORTED', name='encounter_outcome').create(op.get_bind(), checkfirst=True)
    sa.Enum('CHARACTER', 'NPC', 'SYSTEM', name='actor_type').create(op.get_bind(), checkfirst=True)
    sa.Enum('INITIATIVE_ROLL', 'ATTACK', 'DAMAGE', 'HEAL', 'SPELL', 'ABILITY', 'MOVEMENT', 'CONDITION_APPLY', 'CONDITION_REMOVE', 'DEATH', 'TURN_START', 'TURN_END', 'TURN_SKIPPED', 'DM_OVERRIDE', 'CUSTOM', name='combat_action_type').create(op.get_bind(), checkfirst=True)
    sa.Enum('CHARACTER', 'NPC', name='participant_type').create(op.get_bind(), checkfirst=True)
    sa.Enum('ROLLING_INITIATIVE', 'IN_PROGRESS', 'WAITING_RECONNECT', 'PAUSED', 'ENDED', name='encounter_state_status').create(op.get_bind(), checkfirst=True)

    # Recreate tables in forward order
    op.create_table('encounters',
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'READY', 'ACTIVE', 'PAUSED', 'COMPLETED', name='encounter_status'), server_default=sa.text("'DRAFT'"), nullable=False),
    sa.Column('difficulty', sa.Enum('TRIVIAL', 'EASY', 'MEDIUM', 'HARD', 'DEADLY', name='encounter_difficulty'), nullable=True),
    sa.Column('estimated_xp', sa.Integer(), nullable=True),
    sa.Column('outcome', sa.Enum('VICTORY', 'DEFEAT', 'FLED', 'NEGOTIATED', 'ABORTED', name='encounter_outcome'), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], name=op.f('fk_encounters_game_id_games'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_encounters'))
    )
    op.create_index(op.f('ix_encounters_game_id'), 'encounters', ['game_id'], unique=False)
    op.create_table('combat_logs',
    sa.Column('encounter_id', sa.Integer(), nullable=False),
    sa.Column('round_number', sa.Integer(), nullable=False),
    sa.Column('action_type', sa.Enum('INITIATIVE_ROLL', 'ATTACK', 'DAMAGE', 'HEAL', 'SPELL', 'ABILITY', 'MOVEMENT', 'CONDITION_APPLY', 'CONDITION_REMOVE', 'DEATH', 'TURN_START', 'TURN_END', 'TURN_SKIPPED', 'DM_OVERRIDE', 'CUSTOM', name='combat_action_type'), nullable=False),
    sa.Column('actor_type', sa.Enum('CHARACTER', 'NPC', 'SYSTEM', name='actor_type'), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('actor_name', sa.String(length=255), nullable=False),
    sa.Column('target_type', sa.Enum('CHARACTER', 'NPC', 'SYSTEM', name='actor_type'), nullable=True),
    sa.Column('target_id', sa.Integer(), nullable=True),
    sa.Column('target_name', sa.String(length=255), nullable=True),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('result', sa.JSON(), nullable=True),
    sa.Column('created_by_user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_combat_logs_created_by_user_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], name=op.f('fk_combat_logs_encounter_id_encounters'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_combat_logs'))
    )
    op.create_index(op.f('ix_combat_logs_encounter_id'), 'combat_logs', ['encounter_id'], unique=False)
    op.create_table('encounter_participants',
    sa.Column('encounter_id', sa.Integer(), nullable=False),
    sa.Column('participant_type', sa.Enum('CHARACTER', 'NPC', name='participant_type'), nullable=False),
    sa.Column('participant_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.Column('instance_index', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], name=op.f('fk_encounter_participants_encounter_id_encounters'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_encounter_participants'))
    )
    op.create_index(op.f('ix_encounter_participants_encounter_id'), 'encounter_participants', ['encounter_id'], unique=False)
    op.create_table('encounter_states',
    sa.Column('encounter_id', sa.Integer(), nullable=False),
    sa.Column('current_round', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.Column('current_turn_index', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('initiative_order', sa.JSON(), nullable=False),
    sa.Column('combatants_state', sa.JSON(), nullable=False),
    sa.Column('turn_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('ROLLING_INITIATIVE', 'IN_PROGRESS', 'WAITING_RECONNECT', 'PAUSED', 'ENDED', name='encounter_state_status'), server_default=sa.text("'ROLLING_INITIATIVE'"), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], name=op.f('fk_encounter_states_encounter_id_encounters'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_encounter_states'))
    )
    op.create_index(op.f('ix_encounter_states_encounter_id'), 'encounter_states', ['encounter_id'], unique=True)
