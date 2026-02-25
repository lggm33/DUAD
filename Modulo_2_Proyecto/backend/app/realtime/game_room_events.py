"""
Game room event handlers for SocketIO.

Handles joining and leaving game rooms for real-time updates.
"""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room

from app.extensions import db
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.models import GameMembershipStatus, GameRoleInGame, TurnType
from app.domain.npcs.npc_repository import NPCRepository

logger = logging.getLogger(__name__)


def register_game_room_events(socketio, app, shared_state, helpers):
    """Register game room-related SocketIO events."""

    authenticated_users = shared_state["authenticated_users"]
    broadcast_system_message = helpers["broadcast_system_message"]
    get_user_or_error = helpers["get_user_or_error"]

    @socketio.on("join_game")
    def handle_join_game(data):
        """Join a game room for real-time updates."""
        user = get_user_or_error()
        if not user:
            return

        game_id = data.get("game_id")
        if not game_id:
            emit("error", {"code": "INVALID_DATA", "message": "game_id is required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                membership_repo = GameMembershipRepository(session)
                game_repo = GameRepository(session)
                
                membership = membership_repo.get_game_membership_by_game_id_and_user_id(
                    game_id, user["user_id"]
                )

                if not membership or membership.status != GameMembershipStatus.ACTIVE:
                    emit("error", {"code": "NOT_MEMBER", "message": "Not a member of this game"})
                    return

                if user.get("game_id"):
                    leave_room(f"game_{user['game_id']}")
                    leave_room(f"game_{user['game_id']}_dm")

                join_room(f"game_{game_id}")
                
                # If user is DM, also join the DM-only room for private dice rolls
                if membership.role_in_game == GameRoleInGame.DM:
                    join_room(f"game_{game_id}_dm")
                    user["is_dm"] = True
                else:
                    user["is_dm"] = False

                user["game_id"] = game_id

                emit("joined_game", {"game_id": game_id})

                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} joined the chat")
                
                # Send current turn state to the joining user
                game = game_repo.get_game_by_id(game_id)
                if game and (game.current_turn_user_id or game.current_turn_npc_id):
                    turn_data = {
                        "turn_type": game.current_turn_type,
                        "set_by": None  # Historical info not stored
                    }
                    
                    if game.current_turn_type == TurnType.USER:
                        turn_data["user_id"] = game.current_turn_user_id
                        turn_data["character_name"] = game.current_turn_character_name
                    elif game.current_turn_type == TurnType.NPC:
                        turn_data["npc_id"] = game.current_turn_npc_id
                        if game.current_turn_npc:
                            turn_data["character_name"] = game.current_turn_npc.name
                            turn_data["npc_type"] = game.current_turn_npc.npc_type.value
                    
                    emit("turn_update", turn_data)

        except Exception as e:
            logger.error(f"[SocketIO] Error joining game: {e}")
            emit("error", {"code": "JOIN_FAILED", "message": "Failed to join game"})

    @socketio.on("set_turn")
    def handle_set_turn(data):
        """Set the active turn (DM only)."""
        user = get_user_or_error()
        if not user or not user.get("is_dm"):
            emit("error", {"code": "FORBIDDEN", "message": "Only DM can set turns"})
            return

        game_id = data.get("game_id")
        turn_type = data.get("turn_type", "USER")
        
        # Validate turn_type
        if turn_type not in ["USER", "NPC"]:
            emit("error", {"code": "INVALID_DATA", "message": "turn_type must be USER or NPC"})
            return

        if not game_id:
            emit("error", {"code": "INVALID_DATA", "message": "game_id is required"})
            return

        try:
            # Convert game_id to integer
            try:
                game_id = int(game_id)
            except (ValueError, TypeError):
                emit("error", {"code": "INVALID_DATA", "message": "Invalid game_id format"})
                return
            
            with app.app_context():
                session = db.get_session()
                game_repo = GameRepository(session)
                game = game_repo.get_game_by_id(game_id)
                
                if not game:
                    emit("error", {"code": "GAME_NOT_FOUND", "message": "Game not found"})
                    return
                
                turn_data = {
                    "turn_type": turn_type,
                    "set_by": user["user_id"]
                }
                
                if turn_type == "USER":
                    # USER turn logic
                    target_user_id = data.get("user_id")
                    character_name = data.get("character_name")
                    
                    if not target_user_id:
                        emit("error", {"code": "INVALID_DATA", "message": "user_id is required for USER turn"})
                        return
                    
                    try:
                        target_user_id = int(target_user_id)
                    except (ValueError, TypeError):
                        emit("error", {"code": "INVALID_DATA", "message": "Invalid user_id format"})
                        return
                    
                    # Set USER turn
                    game.current_turn_type = TurnType.USER
                    game.current_turn_user_id = target_user_id
                    game.current_turn_character_name = character_name
                    game.current_turn_npc_id = None
                    
                    turn_data["user_id"] = target_user_id
                    turn_data["character_name"] = character_name
                    
                    logger.info(f"[SocketIO] Turn set to user {target_user_id} in game {game_id}")
                    
                elif turn_type == "NPC":
                    # NPC turn logic
                    npc_id = data.get("npc_id")
                    display_name = data.get("display_name")
                    npc_type = data.get("npc_type")
                    
                    if not npc_id:
                        emit("error", {"code": "INVALID_DATA", "message": "npc_id is required for NPC turn"})
                        return
                    
                    try:
                        npc_id = int(npc_id)
                    except (ValueError, TypeError):
                        emit("error", {"code": "INVALID_DATA", "message": "Invalid npc_id format"})
                        return
                    
                    # Validate NPC exists and belongs to this game
                    npc_repo = NPCRepository(session)
                    npc = npc_repo.get_by_id(npc_id)
                    
                    if not npc or npc.game_id != game_id:
                        emit("error", {"code": "NPC_NOT_FOUND", "message": "NPC not found in this game"})
                        return
                    
                    # Set NPC turn
                    game.current_turn_type = TurnType.NPC
                    game.current_turn_npc_id = npc_id
                    game.current_turn_user_id = None
                    game.current_turn_character_name = None
                    
                    turn_data["npc_id"] = npc_id
                    turn_data["character_name"] = display_name or npc.name
                    turn_data["npc_type"] = npc_type or npc.npc_type.value
                    
                    logger.info(f"[SocketIO] Turn set to NPC {npc_id} in game {game_id}")
                
                session.commit()

            # Broadcast turn update to everyone
            emit("turn_update", turn_data, room=f"game_{game_id}")
            
        except Exception as e:
            logger.error(f"[SocketIO] Error setting turn: {e}")
            emit("error", {"code": "SET_TURN_FAILED", "message": "Failed to set turn"})

    @socketio.on("clear_turn")
    def handle_clear_turn(data):
        """Clear the active turn (DM only)."""
        user = get_user_or_error()
        if not user or not user.get("is_dm"):
            emit("error", {"code": "FORBIDDEN", "message": "Only DM can clear turns"})
            return

        game_id = data.get("game_id")
        if not game_id:
            emit("error", {"code": "INVALID_DATA", "message": "game_id is required"})
            return

        try:
            # Convert to integer (frontend sends as string)
            try:
                game_id = int(game_id)
            except (ValueError, TypeError) as e:
                emit("error", {"code": "INVALID_DATA", "message": "Invalid game_id format"})
                return
            
            with app.app_context():
                session = db.get_session()
                game_repo = GameRepository(session)
                game = game_repo.get_game_by_id(game_id)
                
                if not game:
                    emit("error", {"code": "GAME_NOT_FOUND", "message": "Game not found"})
                    return
                
                # Clear turn state from database
                game.current_turn_type = None
                game.current_turn_user_id = None
                game.current_turn_character_name = None
                game.current_turn_npc_id = None
                session.commit()
                
                logger.info(f"[SocketIO] Turn cleared in game {game_id}")

            # Broadcast turn clear to everyone
            emit("turn_update", {
                "turn_type": None,
                "user_id": None,
                "character_name": None,
                "npc_id": None
            }, room=f"game_{game_id}")
            
        except Exception as e:
            logger.error(f"[SocketIO] Error clearing turn: {e}")
            emit("error", {"code": "CLEAR_TURN_FAILED", "message": "Failed to clear turn"})

    @socketio.on("leave_chat")
    def handle_leave_chat(data):
        """Leave the chat room."""
        user = authenticated_users.get(request.sid)
        if not user:
            return

        game_id = data.get("game_id") or user.get("game_id")
        if not game_id:
            return

        try:
            with app.app_context():
                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} left the chat")
                leave_room(f"game_{game_id}")
                user["game_id"] = None
        except Exception as e:
            logger.error(f"[SocketIO] Error in leave_chat: {e}")
            leave_room(f"game_{game_id}")
            user["game_id"] = None

    @socketio.on("leave_game")
    def handle_leave_game(data):
        """Leave the game entirely."""
        user = authenticated_users.get(request.sid)
        if not user:
            return

        game_id = data.get("game_id") or user.get("game_id")
        if not game_id:
            return

        try:
            with app.app_context():
                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} left the game")
                leave_room(f"game_{game_id}")
                user["game_id"] = None
        except Exception as e:
            logger.error(f"[SocketIO] Error in leave_game: {e}")
            leave_room(f"game_{game_id}")
            user["game_id"] = None

