from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin


if TYPE_CHECKING:
    from app.domain.games.models import Game
    from app.domain.users.models import User


class MessageType(str, Enum):
    """Enum for chat message types."""

    USER = "user"
    SYSTEM = "system"
    DICE = "dice"


class ChatMessage(Base, IntPrimaryKeyMixin):
    """Model for chat messages in a game session."""

    __tablename__ = "chat_messages"

    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MessageType.USER.value
    )
    character_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", lazy="joined")
    user: Mapped[Optional["User"]] = relationship("User", lazy="joined")

