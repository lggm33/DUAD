from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.chat.models import ChatMessage, MessageType


class ChatRepository:
    """Repository for managing chat message persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, game_id: int, user_id: int, content: str) -> ChatMessage:
        """
        Create a new user chat message.
        """
        message = ChatMessage(
            game_id=game_id,
            user_id=user_id,
            content=content,
            message_type=MessageType.USER.value,
        )
        self._session.add(message)
        self._session.flush()
        return message

    def create_system_message(self, game_id: int, content: str) -> ChatMessage:
        """
        Create a new system chat message (no user_id).
        """
        message = ChatMessage(
            game_id=game_id,
            user_id=None,
            content=content,
            message_type=MessageType.SYSTEM.value,
        )
        self._session.add(message)
        self._session.flush()
        return message

    def get_by_game(self, game_id: int, limit: int = 50) -> list[ChatMessage]:
        """
        Get messages for a game, ordered by creation time (oldest first).
        Returns the last N messages.
        """
        return (
            self._session.query(ChatMessage)
            .filter(ChatMessage.game_id == game_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )[::-1]  # Reverse to get oldest first

    def get_by_id(self, message_id: int) -> ChatMessage | None:
        """
        Get a message by its ID.
        """
        return self._session.query(ChatMessage).filter_by(id=message_id).first()

