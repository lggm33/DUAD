"""Add message_type to chat_messages and make user_id nullable

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2025-12-31

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add message_type column with default value 'user'
    op.add_column(
        "chat_messages",
        sa.Column("message_type", sa.String(20), nullable=False, server_default="user"),
    )

    # Make user_id nullable for system messages
    op.alter_column(
        "chat_messages",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Make user_id not nullable again (delete system messages first)
    op.execute("DELETE FROM chat_messages WHERE user_id IS NULL")
    op.alter_column(
        "chat_messages",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Remove message_type column
    op.drop_column("chat_messages", "message_type")

