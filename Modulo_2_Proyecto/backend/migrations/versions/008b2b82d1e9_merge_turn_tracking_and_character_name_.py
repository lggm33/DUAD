"""merge turn tracking and character name migrations

Revision ID: 008b2b82d1e9
Revises: 69a5d44b8ba0, a1b2c3d4e5f7
Create Date: 2026-01-25 11:54:28.075060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008b2b82d1e9'
down_revision: Union[str, Sequence[str], None] = ('69a5d44b8ba0', 'a1b2c3d4e5f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
