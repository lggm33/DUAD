"""Add ruleset_templates table

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2025-12-31

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for ruleset_system_type
    ruleset_system_type = sa.Enum(
        "DND_5E", "PATHFINDER_2E", "CUSTOM",
        name="ruleset_system_type"
    )

    op.create_table(
        "ruleset_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_type", ruleset_system_type, nullable=False),
        sa.Column("base_rules", sa.JSON(), nullable=False),
        sa.Column("is_system_provided", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_ruleset_templates_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ruleset_templates")),
    )
    op.create_index(
        op.f("ix_ruleset_templates_created_by_user_id"),
        "ruleset_templates",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_ruleset_templates_created_by_user_id"),
        table_name="ruleset_templates",
    )
    op.drop_table("ruleset_templates")

    # Drop enum type
    sa.Enum(name="ruleset_system_type").drop(op.get_bind(), checkfirst=True)

