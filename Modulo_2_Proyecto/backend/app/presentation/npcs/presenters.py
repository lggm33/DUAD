"""
Presenter for NPC entities.

Transforms NPC domain objects into API response dictionaries.
"""

from typing import Any

from app.presentation.base import Presenter
from app.domain.npcs.models import NPC


class NPCPresenter(Presenter):
    """Presenter for NPC entities."""

    @staticmethod
    def public(npc: NPC) -> dict[str, Any]:
        """
        Returns a public dictionary for an NPC.

        Includes full NPC data for DM view.
        """
        return {
            "id": npc.id,
            "game_id": npc.game_id,
            "name": npc.name,
            "npc_type": npc.npc_type.value,
            "status": npc.status.value,
            "description": npc.description,
            "stats": npc.stats,
            "data": npc.data,
            "created_at": npc.created_at.isoformat() if npc.created_at else None,
            "updated_at": npc.updated_at.isoformat() if npc.updated_at else None,
        }

    @staticmethod
    def summary(npc: NPC) -> dict[str, Any]:
        """
        Returns a summary dictionary for an NPC.

        Useful for listing NPCs without full data.
        """
        return {
            "id": npc.id,
            "game_id": npc.game_id,
            "name": npc.name,
            "npc_type": npc.npc_type.value,
            "status": npc.status.value,
            "description": npc.description,
            "created_at": npc.created_at.isoformat() if npc.created_at else None,
        }

    @staticmethod
    def player_view(npc: NPC) -> dict[str, Any]:
        """
        Returns a limited view for players.

        Players see less information about NPCs than the DM.
        """
        return {
            "id": npc.id,
            "game_id": npc.game_id,
            "name": npc.name,
            "npc_type": npc.npc_type.value,
            "status": npc.status.value,
            "description": npc.description,
        }

    @staticmethod
    def collection(npcs: list[NPC]) -> list[dict[str, Any]]:
        """Returns a list of public dictionaries for a collection of NPCs."""
        return [NPCPresenter.public(npc) for npc in npcs]

    @staticmethod
    def summary_collection(npcs: list[NPC]) -> list[dict[str, Any]]:
        """Returns a list of summary dictionaries for a collection of NPCs."""
        return [NPCPresenter.summary(npc) for npc in npcs]

    @staticmethod
    def player_collection(npcs: list[NPC]) -> list[dict[str, Any]]:
        """Returns a list of player-view dictionaries for a collection of NPCs."""
        return [NPCPresenter.player_view(npc) for npc in npcs]

