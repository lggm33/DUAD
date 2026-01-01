"""
Chat event handlers for SocketIO.

Handles real-time chat messages within game rooms.
"""

import logging
from flask_socketio import emit

from app.extensions import db
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService

logger = logging.getLogger(__name__)


def register_chat_events(socketio, app, shared_state, helpers):
    """Register chat-related SocketIO events."""

    get_user_or_error = helpers["get_user_or_error"]

    @socketio.on("chat_message")
    def handle_chat_message(data):
        """Handle incoming chat message."""
        user = get_user_or_error()
        if not user:
            return

        game_id = data.get("game_id")
        content = data.get("content", "").strip()

        if not game_id or not content:
            emit("error", {"code": "INVALID_DATA", "message": "game_id and content are required"})
            return

        if user.get("game_id") != game_id:
            emit("error", {"code": "NOT_IN_GAME", "message": "You are not in this game"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                chat_repo = ChatRepository(session)
                chat_service = ChatService(chat_repo)
                message = chat_service.send_message(game_id, user["user_id"], content)
                message_data = chat_service.message_to_dict(message)
                session.commit()

                emit("chat_message", message_data, room=f"game_{game_id}")

        except ValueError as e:
            emit("error", {"code": "VALIDATION_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error sending chat: {e}")
            emit("error", {"code": "CHAT_FAILED", "message": "Failed to send message"})

