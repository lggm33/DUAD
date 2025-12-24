from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


if TYPE_CHECKING:
    from app.domain.users.models import User


class GameStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class Game(Base, IntPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "games"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dm_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[GameStatus] = mapped_column(
        SQLEnum(GameStatus, name="game_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    # Relationships
    dm_user: Mapped["User"] = relationship("User", back_populates="games")  # type: ignore