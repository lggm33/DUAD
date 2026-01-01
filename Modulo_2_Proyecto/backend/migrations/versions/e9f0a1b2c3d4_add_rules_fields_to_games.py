"""Add rules fields to games table

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2025-12-31

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for character_creation_mode
    character_creation_mode = sa.Enum(
        "OPEN", "DM_APPROVAL",
        name="character_creation_mode"
    )
    # Actually create the enum in the database BEFORE using it
    character_creation_mode.create(op.get_bind(), checkfirst=True)

    # Add ruleset_template_id column
    op.add_column(
        "games",
        sa.Column(
            "ruleset_template_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        op.f("fk_games_ruleset_template_id_ruleset_templates"),
        "games",
        "ruleset_templates",
        ["ruleset_template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for ruleset_template_id
    op.create_index(
        op.f("ix_games_ruleset_template_id"),
        "games",
        ["ruleset_template_id"],
        unique=False,
    )

    # Add custom_rules column (JSON)
    op.add_column(
        "games",
        sa.Column(
            "custom_rules",
            sa.JSON(),
            nullable=True,
        ),
    )

    # Add character_creation_mode column
    op.add_column(
        "games",
        sa.Column(
            "character_creation_mode",
            character_creation_mode,
            nullable=False,
            server_default="OPEN",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop character_creation_mode column
    op.drop_column("games", "character_creation_mode")

    # Drop custom_rules column
    op.drop_column("games", "custom_rules")

    # Drop index
    op.drop_index(
        op.f("ix_games_ruleset_template_id"),
        table_name="games",
    )

    # Drop foreign key constraint
    op.drop_constraint(
        op.f("fk_games_ruleset_template_id_ruleset_templates"),
        "games",
        type_="foreignkey",
    )

    # Drop ruleset_template_id column
    op.drop_column("games", "ruleset_template_id")

    # Drop enum type
    sa.Enum(name="character_creation_mode").drop(op.get_bind(), checkfirst=True)

