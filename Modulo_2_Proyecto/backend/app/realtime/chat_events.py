"""
Chat event handlers for SocketIO.

Handles real-time chat messages within game rooms.
"""

import logging
from flask_socketio import emit

from app.extensions import db
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService
from app.domain.characters.character_service import CharacterService
from app.domain.characters.character_repository import CharacterRepository
from app.domain.characters.models import CharacterStatus
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository

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
        message_type = data.get("message_type", "user")

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

                # Get user's active character in this game
                character_repo = CharacterRepository(session)
                game_repo = GameRepository(session)
                membership_repo = GameMembershipRepository(session)
                character_service = CharacterService(character_repo, game_repo, membership_repo)
                character = character_service.get_user_approved_character_in_game(game_id, user["user_id"])
                # Use character name if approved character exists
                character_name = character.name if character else None

                message = chat_service.send_message(
                    game_id=game_id, 
                    user_id=user["user_id"], 
                    content=content, 
                    character_name=character_name,
                    message_type=message_type
                )
                message_data = chat_service.message_to_dict(message)
                session.commit()

                # Privacy logic for dice rolls
                if message_type == "dice":
                    if user.get("is_dm"):
                        # DM dice rolls are ONLY visible to the DM
                        emit("chat_message", message_data, to=request.sid)
                    else:
                        # Player dice rolls are visible to the Player AND the DM
                        emit("chat_message", message_data, to=request.sid)
                        emit("chat_message", message_data, room=f"game_{game_id}_dm")
                else:
                    # Regular messages are visible to everyone in the game
                    emit("chat_message", message_data, room=f"game_{game_id}")

        except ValueError as e:
            emit("error", {"code": "VALIDATION_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error sending chat: {e}")
            emit("error", {"code": "CHAT_FAILED", "message": "Failed to send message"})

