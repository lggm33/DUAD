"""
Chat event handlers for SocketIO.

Handles real-time chat messages within game rooms.
"""

import logging
from flask import request
from flask_socketio import emit

from app.extensions import db
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService
from app.domain.characters.character_service import CharacterService
from app.domain.characters.character_repository import CharacterRepository
from app.domain.characters.models import CharacterStatus
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import TurnType

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

                # Privacy logic for dice rolls - validate BEFORE saving
                if message_type == "dice":
                    # Get current turn from game
                    game = game_repo.get_game_by_id(game_id)
                    current_turn_type = game.current_turn_type if game else None
                    current_turn_user_id = game.current_turn_user_id if game else None
                    npc_id = data.get("npc_id")  # NPC context from frontend
                    
                    if user.get("is_dm"):
                        # DM can always roll dice
                        pass
                    else:
                        # Players validation
                        if current_turn_type == TurnType.NPC:
                            # NPC turn: players cannot roll
                            emit("error", {
                                "code": "NOT_YOUR_TURN",
                                "message": "It's an NPC's turn. Only the DM can roll dice."
                            })
                            return
                        elif current_turn_type == TurnType.USER:
                            # User turn: only that user can roll
                            if current_turn_user_id != user["user_id"]:
                                emit("error", {
                                    "code": "NOT_YOUR_TURN",
                                    "message": "You can only roll dice during your turn"
                                })
                                return
                        else:
                            # No turn assigned: only DM can roll
                            emit("error", {
                                "code": "NOT_YOUR_TURN",
                                "message": "No turn is currently assigned. Only the DM can roll dice."
                            })
                            return

                # Save message after validation
                message = chat_service.send_message(
                    game_id=game_id, 
                    user_id=user["user_id"], 
                    content=content, 
                    character_name=character_name,
                    message_type=message_type
                )
                message_data = chat_service.message_to_dict(message)
                session.commit()

                # Broadcast logic based on message type
                if message_type == "dice":
                    # Check if this is an NPC roll
                    is_npc_roll = npc_id is not None
                    
                    if is_npc_roll:
                        # NPC dice rolls are ONLY visible to the DM (always private)
                        emit("chat_message", message_data)  # Only to sender (DM)
                    elif user.get("is_dm"):
                        # DM dice rolls (not NPC) are ONLY visible to the DM
                        emit("chat_message", message_data)  # Only to sender
                    else:
                        # Player dice rolls (validated above: only during their turn)
                        # Visible to the Player AND the DM
                        emit("chat_message", message_data)  # To sender
                        emit("chat_message", message_data, room=f"game_{game_id}_dm")
                else:
                    # Regular messages are visible to everyone in the game
                    emit("chat_message", message_data, room=f"game_{game_id}")

        except ValueError as e:
            emit("error", {"code": "VALIDATION_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error sending chat: {e}")
            emit("error", {"code": "CHAT_FAILED", "message": "Failed to send message"})

