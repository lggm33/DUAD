from __future__ import annotations

from typing import Optional, TypedDict

from app.domain.chat.models import ChatMessage, MessageType
from app.domain.chat.chat_repository import ChatRepository


class ChatMessageData(TypedDict):
    """Data transfer object for chat messages."""

    id: int
    game_id: int
    user_id: Optional[int]
    username: Optional[str]
    name: Optional[str]
    content: str
    message_type: str
    created_at: str


class ChatService:
    """Service for managing chat use cases."""

    def __init__(self, chat_repository: ChatRepository) -> None:
        self._chat_repository = chat_repository

    def send_message(self, game_id: int, user_id: int, content: str) -> ChatMessage:
        """
        Send a new user chat message.
        Persists the message and returns it.
        """
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        message = self._chat_repository.create(
            game_id=game_id,
            user_id=user_id,
            content=content.strip(),
        )
        return message

    def send_system_message(self, game_id: int, content: str) -> ChatMessage:
        """
        Send a system message (no user associated).
        Persists the message and returns it.
        """
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        message = self._chat_repository.create_system_message(
            game_id=game_id,
            content=content.strip(),
        )
        return message

    def get_history(self, game_id: int, limit: int = 50) -> list[ChatMessage]:
        """
        Get chat history for a game.
        Returns messages ordered by creation time (oldest first).
        """
        return self._chat_repository.get_by_game(game_id, limit)

    def message_to_dict(self, message: ChatMessage) -> ChatMessageData:
        """
        Convert a ChatMessage to a dictionary for JSON serialization.
        Handles both user messages and system messages (where user is None).
        """
        is_system = message.message_type == MessageType.SYSTEM.value

        return ChatMessageData(
            id=message.id,
            game_id=message.game_id,
            user_id=message.user_id,
            username=None if is_system else message.user.username,
            name="System" if is_system else message.user.name,
            content=message.content,
            message_type=message.message_type,
            created_at=message.created_at.isoformat(),
        )

