"""
Service for NPC business logic.

Handles NPC creation, management, and conversion between PC/NPC.
"""

from __future__ import annotations

from typing import Any, Optional

from app.domain.npcs.models import NPC, NPCStatus, NPCType
from app.domain.npcs.npc_repository import NPCRepository
from app.domain.characters.models import Character, CharacterStatus
from app.domain.characters.character_repository import CharacterRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameRoleInGame, GameMembershipStatus


class NPCService:
    """Service for NPC operations."""

    def __init__(
        self,
        npc_repository: NPCRepository,
        character_repository: CharacterRepository,
        game_repository: GameRepository,
        game_membership_repository: GameMembershipRepository,
    ) -> None:
        self._npc_repo = npc_repository
        self._character_repo = character_repository
        self._game_repo = game_repository
        self._membership_repo = game_membership_repository

    # =========================================================================
    # Authorization helpers
    # =========================================================================

    def _verify_is_dm(self, game_id: int, user_id: int) -> None:
        """Verify user is the DM of the game."""
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise ValueError("Only the DM can manage NPCs")

    def _verify_game_exists(self, game_id: int) -> None:
        """Verify game exists."""
        game = self._game_repo.get_game_by_id(game_id)
        if not game:
            raise ValueError("Game not found")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_npc(
        self,
        game_id: int,
        dm_user_id: int,
        name: str,
        npc_type: NPCType,
        description: Optional[str] = None,
        stats: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> NPC:
        """
        Create a new NPC.

        Args:
            game_id: The game ID
            dm_user_id: The DM user ID (must be game's DM)
            name: NPC name
            npc_type: Type of NPC (ALLY, ENEMY, etc.)
            description: Optional description
            stats: Combat stats (HP, AC, etc.)
            data: Full character data

        Returns:
            The created NPC

        Raises:
            ValueError: If user is not the DM
        """
        self._verify_game_exists(game_id)
        self._verify_is_dm(game_id, dm_user_id)

        npc = NPC(
            game_id=game_id,
            name=name,
            npc_type=npc_type,
            status=NPCStatus.ACTIVE,
            description=description,
            stats=stats or {},
            data=data or {},
        )

        return self._npc_repo.create(npc)

    def update_npc(
        self,
        npc_id: int,
        dm_user_id: int,
        name: Optional[str] = None,
        npc_type: Optional[NPCType] = None,
        status: Optional[NPCStatus] = None,
        description: Optional[str] = None,
        stats: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> NPC:
        """
        Update an NPC.

        Args:
            npc_id: The NPC ID
            dm_user_id: The DM user ID
            name: New name (optional)
            npc_type: New type (optional)
            status: New status (optional)
            description: New description (optional)
            stats: New stats (optional)
            data: New data (optional)

        Returns:
            The updated NPC

        Raises:
            ValueError: If NPC not found or user is not the DM
        """
        npc = self._npc_repo.get_by_id(npc_id)
        if not npc:
            raise ValueError("NPC not found")

        self._verify_is_dm(npc.game_id, dm_user_id)

        if name is not None:
            npc.name = name
        if npc_type is not None:
            npc.npc_type = npc_type
        if status is not None:
            npc.status = status
        if description is not None:
            npc.description = description
        if stats is not None:
            npc.stats = stats
        if data is not None:
            npc.data = data

        return npc

    def delete_npc(self, npc_id: int, dm_user_id: int) -> bool:
        """
        Delete an NPC.

        Args:
            npc_id: The NPC ID
            dm_user_id: The DM user ID

        Returns:
            True if deleted

        Raises:
            ValueError: If NPC not found or user is not the DM
        """
        npc = self._npc_repo.get_by_id(npc_id)
        if not npc:
            raise ValueError("NPC not found")

        self._verify_is_dm(npc.game_id, dm_user_id)
        self._npc_repo.delete(npc)
        return True

    def get_npc(self, npc_id: int, user_id: int) -> Optional[NPC]:
        """
        Get an NPC by ID.

        Any game member can view NPCs.

        Args:
            npc_id: The NPC ID
            user_id: The requesting user ID

        Returns:
            The NPC if accessible
        """
        npc = self._npc_repo.get_by_id(npc_id)
        if not npc:
            return None

        # Verify user is a member of the game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            npc.game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            return None

        return npc

    def get_game_npcs(
        self,
        game_id: int,
        user_id: int,
        active_only: bool = False,
        npc_type: Optional[NPCType] = None,
    ) -> list[NPC]:
        """
        Get NPCs in a game.

        Args:
            game_id: The game ID
            user_id: The requesting user ID
            active_only: Only return active NPCs
            npc_type: Filter by type

        Returns:
            List of NPCs
        """
        # Verify user is a member
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            return []

        if npc_type:
            return self._npc_repo.get_by_type(game_id, npc_type)
        elif active_only:
            return self._npc_repo.get_active_by_game_id(game_id)
        else:
            return self._npc_repo.get_by_game_id(game_id)

    def revive_npc(self, npc_id: int, dm_user_id: int) -> NPC:
        """Revive a defeated NPC back to active status."""
        npc = self._npc_repo.get_by_id(npc_id)
        if not npc:
            raise ValueError("NPC not found")

        if npc.status not in (NPCStatus.DEFEATED, NPCStatus.RETIRED):
            raise ValueError("NPC is not defeated or retired")

        return self.update_npc(npc_id, dm_user_id, status=NPCStatus.ACTIVE)

