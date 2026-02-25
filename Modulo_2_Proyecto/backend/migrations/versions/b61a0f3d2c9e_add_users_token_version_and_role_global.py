"""Add users.token_version and align role semantics to global RBAC.

Revision ID: b61a0f3d2c9e
Revises: 407a4af0c6be
Create Date: 2025-12-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b61a0f3d2c9e"
down_revision: Union[str, Sequence[str], None] = "407a4af0c6be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add token version for JWT invalidation / refresh rotation.
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )

    # Align existing data to global RBAC roles (ADMIN/USER).
    # Previous default was 'player'. We map any unknown/legacy role to USER.
    op.execute(
        """
        UPDATE users
        SET role = 'USER'
        WHERE role IS NULL
           OR role = ''
           OR role NOT IN ('ADMIN', 'USER');
        """
    )

    # Make USER the default role for new users.
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default=sa.text("'USER'"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Restore previous default semantics.
    op.alter_column(
        "users",
        "role",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default=sa.text("'player'"),
    )

    # Best-effort data rollback (keep ADMIN intact).
    op.execute(
        """
        UPDATE users
        SET role = 'player'
        WHERE role = 'USER';
        """
    )

    op.drop_column("users", "token_version")

