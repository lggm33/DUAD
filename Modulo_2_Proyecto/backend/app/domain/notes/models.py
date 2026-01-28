from __future__ import annotations
from enum import Enum
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.games.models import Game
    from app.domain.users.models import User

class NoteVisibility(str, Enum):
    PRIVATE = "PRIVATE"
    SHARED = "SHARED"

class GameNote(Base, IntPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "game_notes"
    
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[NoteVisibility] = mapped_column(SQLEnum(NoteVisibility), nullable=False, default=NoteVisibility.PRIVATE)
    
    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="notes")
    user: Mapped["User"] = relationship("User", back_populates="notes")
