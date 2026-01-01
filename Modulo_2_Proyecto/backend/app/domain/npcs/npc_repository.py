"""
Repository for NPC persistence operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.npcs.models import NPC, NPCStatus, NPCType


class NPCRepository:
    """Repository for managing NPC persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, npc: NPC) -> NPC:
        """Create a new NPC."""
        self._session.add(npc)
        self._session.flush()
        return npc

    def get_by_id(self, npc_id: int) -> Optional[NPC]:
        """Get an NPC by ID."""
        return self._session.query(NPC).filter_by(id=npc_id).first()

    def get_by_game_id(self, game_id: int) -> list[NPC]:
        """Get all NPCs in a game."""
        return self._session.query(NPC).filter_by(game_id=game_id).all()

    def get_active_by_game_id(self, game_id: int) -> list[NPC]:
        """Get all active NPCs in a game."""
        return (
            self._session.query(NPC)
            .filter_by(game_id=game_id, status=NPCStatus.ACTIVE)
            .all()
        )

    def get_by_type(self, game_id: int, npc_type: NPCType) -> list[NPC]:
        """Get NPCs of a specific type in a game."""
        return (
            self._session.query(NPC)
            .filter_by(game_id=game_id, npc_type=npc_type)
            .all()
        )

    def get_enemies_for_encounter(self, game_id: int) -> list[NPC]:
        """Get active enemies and bosses for encounters."""
        return (
            self._session.query(NPC)
            .filter(
                NPC.game_id == game_id,
                NPC.status == NPCStatus.ACTIVE,
                NPC.npc_type.in_([NPCType.ENEMY, NPCType.BOSS]),
            )
            .all()
        )

    def get_converted_from_character(self, character_id: int) -> Optional[NPC]:
        """Get NPC that was converted from a specific character."""
        return (
            self._session.query(NPC)
            .filter_by(converted_from_character_id=character_id)
            .first()
        )

    def delete(self, npc: NPC) -> None:
        """Delete an NPC."""
        self._session.delete(npc)
        self._session.flush()

