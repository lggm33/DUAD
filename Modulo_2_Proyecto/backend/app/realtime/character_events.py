"""
Character event handlers for SocketIO.

Provides helper functions to emit character-related events
to game rooms for real-time updates on character approval workflow.
"""

import logging
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)


class CharacterEventEmitter:
    """
    Emitter for character-related SocketIO events.

    Used by HTTP routes to broadcast character status changes
    to all connected clients in a game room.
    """

    _socketio: SocketIO | None = None

    @classmethod
    def init(cls, socketio: SocketIO) -> None:
        """Initialize the emitter with the SocketIO instance."""
        cls._socketio = socketio
        logger.info("[CharacterEvents] Emitter initialized with SocketIO instance")

    @classmethod
    def emit_character_submitted(
        cls,
        game_id: int,
        character_id: int,
        character_name: str,
        player_name: str,
        user_id: int,
    ) -> None:
        """
        Emit event when a character is submitted for approval.

        Notifies the DM that a new character needs review.
        """
        logger.info(
            f"[CharacterEvents] Attempting to emit character:submitted for {character_name} in game {game_id}"
        )
        if not cls._socketio:
            logger.error("[CharacterEvents] SocketIO not initialized - cannot emit character:submitted")
            return

        cls._socketio.emit(
            "character:submitted",
            {
                "character_id": character_id,
                "character_name": character_name,
                "player_name": player_name,
                "user_id": user_id,
                "game_id": game_id,
            },
            room=f"game_{game_id}",
        )
        logger.info(
            f"[CharacterEvents] Successfully emitted character:submitted for {character_name} in game {game_id}"
        )

    @classmethod
    def emit_character_approved(
        cls,
        game_id: int,
        character_id: int,
        character_name: str,
        user_id: int,
        feedback: str | None = None,
    ) -> None:
        """
        Emit event when a character is approved by the DM.

        Notifies the player that their character has been approved.
        """
        logger.info(
            f"[CharacterEvents] Attempting to emit character:approved for {character_name} in game {game_id}"
        )
        if not cls._socketio:
            logger.error("[CharacterEvents] SocketIO not initialized - cannot emit character:approved")
            return

        cls._socketio.emit(
            "character:approved",
            {
                "character_id": character_id,
                "character_name": character_name,
                "user_id": user_id,
                "game_id": game_id,
                "feedback": feedback,
            },
            room=f"game_{game_id}",
        )
        logger.info(
            f"[CharacterEvents] Successfully emitted character:approved for {character_name} in game {game_id}"
        )

    @classmethod
    def emit_character_rejected(
        cls,
        game_id: int,
        character_id: int,
        character_name: str,
        user_id: int,
        feedback: str,
    ) -> None:
        """
        Emit event when a character is rejected by the DM.

        Notifies the player that their character needs changes.
        """
        logger.info(
            f"[CharacterEvents] Attempting to emit character:rejected for {character_name} in game {game_id}"
        )
        if not cls._socketio:
            logger.error("[CharacterEvents] SocketIO not initialized - cannot emit character:rejected")
            return

        cls._socketio.emit(
            "character:rejected",
            {
                "character_id": character_id,
                "character_name": character_name,
                "user_id": user_id,
                "game_id": game_id,
                "feedback": feedback,
            },
            room=f"game_{game_id}",
        )
        logger.info(
            f"[CharacterEvents] Successfully emitted character:rejected for {character_name} in game {game_id}"
        )


def register_character_events(socketio, app, shared_state, helpers):
    """
    Register character-related SocketIO events.

    Currently only initializes the emitter since character events
    are emitted from HTTP routes rather than SocketIO handlers.
    """
    CharacterEventEmitter.init(socketio)
    logger.info("[CharacterEvents] Character events registered")

