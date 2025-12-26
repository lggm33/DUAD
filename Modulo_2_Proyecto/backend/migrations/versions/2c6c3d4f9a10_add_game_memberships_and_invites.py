"""Add game memberships and invites

Revision ID: 2c6c3d4f9a10
Revises: 098118c1aaca
Create Date: 2025-12-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2c6c3d4f9a10"
down_revision: Union[str, Sequence[str], None] = "098118c1aaca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Note:
    # We create Postgres enum types explicitly in an idempotent way.
    # Then we reference them in columns with create_type=False to avoid SQLAlchemy trying
    # to create them again during table creation.
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE game_role_in_game AS ENUM ('PLAYER', 'DM');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE game_membership_status AS ENUM ('ACTIVE', 'LEFT', 'KICKED');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    role_enum = postgresql.ENUM("PLAYER", "DM", name="game_role_in_game", create_type=False)
    membership_status_enum = postgresql.ENUM(
        "ACTIVE", "LEFT", "KICKED", name="game_membership_status", create_type=False
    )

    op.create_table(
        "game_memberships",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_in_game", role_enum, nullable=False),
        sa.Column(
            "status",
            membership_status_enum,
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], name=op.f("fk_game_memberships_game_id_games"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_game_memberships_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_memberships")),
        sa.UniqueConstraint("user_id", "game_id", name="uq_game_memberships_user_id_game_id"),
    )
    op.create_index(op.f("ix_game_memberships_game_id"), "game_memberships", ["game_id"], unique=False)
    op.create_index(op.f("ix_game_memberships_user_id"), "game_memberships", ["user_id"], unique=False)

    op.create_table(
        "game_invites",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_game_invites_created_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], name=op.f("fk_game_invites_game_id_games"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_game_invites")),
    )
    op.create_index(op.f("ix_game_invites_game_id"), "game_invites", ["game_id"], unique=False)
    op.create_index(op.f("ix_game_invites_created_by_user_id"), "game_invites", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_game_invites_code"), "game_invites", ["code"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_game_invites_code"), table_name="game_invites")
    op.drop_index(op.f("ix_game_invites_created_by_user_id"), table_name="game_invites")
    op.drop_index(op.f("ix_game_invites_game_id"), table_name="game_invites")
    op.drop_table("game_invites")

    op.drop_index(op.f("ix_game_memberships_user_id"), table_name="game_memberships")
    op.drop_index(op.f("ix_game_memberships_game_id"), table_name="game_memberships")
    op.drop_table("game_memberships")

    # Drop enum types (safe if they are already missing)
    op.execute("DROP TYPE IF EXISTS game_membership_status;")
    op.execute("DROP TYPE IF EXISTS game_role_in_game;")


