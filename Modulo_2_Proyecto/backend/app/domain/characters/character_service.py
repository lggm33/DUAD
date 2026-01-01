"""
Service for Character business logic.

Handles character creation, validation, approval workflow,
and conversion to NPC.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from app.domain.characters.models import Character, CharacterStatus
from app.domain.characters.character_repository import CharacterRepository
from app.domain.games.models import Game
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameMembershipStatus, GameRoleInGame


class CharacterData(TypedDict, total=False):
    """TypedDict for character data structure."""

    name: str
    race: str
    character_class: str
    level: int
    attributes: dict[str, int]
    background: str
    backstory: str
    equipment: list[str]
    skills: list[str]
    features: list[str]


class CharacterValidationError(Exception):
    """Raised when character validation fails."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []


class CharacterService:
    """Service for character operations."""

    def __init__(
        self,
        character_repository: CharacterRepository,
        game_repository: GameRepository,
        game_membership_repository: GameMembershipRepository,
    ) -> None:
        self._character_repo = character_repository
        self._game_repo = game_repository
        self._membership_repo = game_membership_repository

    def create_character(
        self,
        game_id: int,
        user_id: int,
        name: str,
        data: dict[str, Any],
    ) -> Character:
        """
        Create a new character for a player in a game.

        Args:
            game_id: The game ID
            user_id: The user creating the character
            name: Character name
            data: Character data (class, race, stats, etc.)

        Returns:
            The created character in DRAFT status

        Raises:
            ValueError: If user already has a character in this game
            ValueError: If user is not a member of the game
        """
        # Verify user is an active member of the game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise ValueError("User is not an active member of this game")

        # Check if user already has a character in this game
        existing = self._character_repo.get_by_game_and_user(game_id, user_id)
        if existing:
            raise ValueError("User already has a character in this game")

        character = Character(
            game_id=game_id,
            user_id=user_id,
            name=name,
            status=CharacterStatus.DRAFT,
            data=data,
        )

        return self._character_repo.create(character)

    def update_character(
        self,
        character_id: int,
        user_id: int,
        name: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> Character:
        """
        Update a character's data.

        Only the owner can update, and only if the character is editable
        (DRAFT or REJECTED status).

        Args:
            character_id: The character ID
            user_id: The user attempting to update
            name: New name (optional)
            data: New data (optional)

        Returns:
            The updated character

        Raises:
            ValueError: If character not found, not owned, or not editable
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise ValueError("Character not found")

        if character.user_id != user_id:
            raise ValueError("You can only update your own character")

        if not character.is_editable():
            raise ValueError(
                f"Character cannot be edited in status: {character.status.value}"
            )

        if name is not None:
            character.name = name
        if data is not None:
            character.data = data

        # Clear any previous rejection feedback when player updates
        if character.status == CharacterStatus.REJECTED:
            character.dm_feedback = None
            character.status = CharacterStatus.DRAFT

        return character

    def submit_for_approval(self, character_id: int, user_id: int) -> Character:
        """
        Submit a character for DM approval.

        Args:
            character_id: The character ID
            user_id: The user submitting

        Returns:
            The character with PENDING_APPROVAL status

        Raises:
            ValueError: If character not found, not owned, or not in DRAFT status
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise ValueError("Character not found")

        if character.user_id != user_id:
            raise ValueError("You can only submit your own character")

        if character.status not in (CharacterStatus.DRAFT, CharacterStatus.REJECTED):
            raise ValueError("Character must be in DRAFT or REJECTED status to submit")

        # Get game to check if approval is required
        game = self._game_repo.get_game_by_id(character.game_id)
        if not game:
            raise ValueError("Game not found")

        if game.requires_character_approval():
            character.status = CharacterStatus.PENDING_APPROVAL
            character.dm_feedback = None
        else:
            # Auto-approve if game doesn't require DM approval
            character.status = CharacterStatus.APPROVED

        return character

    def approve_character(
        self,
        character_id: int,
        dm_user_id: int,
        feedback: Optional[str] = None,
    ) -> Character:
        """
        DM approves a character.

        Args:
            character_id: The character ID
            dm_user_id: The DM user ID
            feedback: Optional approval feedback

        Returns:
            The approved character

        Raises:
            ValueError: If not authorized or character not pending
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise ValueError("Character not found")

        # Verify the user is the DM of this game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            character.game_id, dm_user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise ValueError("Only the DM can approve characters")

        if character.status != CharacterStatus.PENDING_APPROVAL:
            raise ValueError("Character is not pending approval")

        character.status = CharacterStatus.APPROVED
        character.dm_feedback = feedback

        return character

    def reject_character(
        self,
        character_id: int,
        dm_user_id: int,
        feedback: str,
    ) -> Character:
        """
        DM rejects a character with feedback.

        Args:
            character_id: The character ID
            dm_user_id: The DM user ID
            feedback: Required rejection reason

        Returns:
            The rejected character

        Raises:
            ValueError: If not authorized or character not pending
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise ValueError("Character not found")

        if not feedback or not feedback.strip():
            raise ValueError("Feedback is required when rejecting a character")

        # Verify the user is the DM of this game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            character.game_id, dm_user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise ValueError("Only the DM can reject characters")

        if character.status != CharacterStatus.PENDING_APPROVAL:
            raise ValueError("Character is not pending approval")

        character.status = CharacterStatus.REJECTED
        character.dm_feedback = feedback.strip()

        return character

    def get_character(self, character_id: int, user_id: int) -> Optional[Character]:
        """
        Get a character by ID.

        Players can only see their own characters or approved characters
        in games they're members of.

        Args:
            character_id: The character ID
            user_id: The requesting user ID

        Returns:
            The character if accessible, None otherwise
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            return None

        # Owner can always see their own character
        if character.user_id == user_id:
            return character

        # Check if user is a member of the same game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            character.game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            return None

        # DM can see all characters in their game
        if membership.role_in_game == GameRoleInGame.DM:
            return character

        # Other players can only see approved characters
        if character.status == CharacterStatus.APPROVED:
            return character

        return None

    def get_user_character_in_game(
        self,
        game_id: int,
        user_id: int,
    ) -> Optional[Character]:
        """Get the user's character in a specific game."""
        return self._character_repo.get_by_game_and_user(game_id, user_id)

    def get_game_characters(
        self,
        game_id: int,
        user_id: int,
        include_pending: bool = False,
    ) -> list[Character]:
        """
        Get characters in a game visible to the user.

        Args:
            game_id: The game ID
            user_id: The requesting user ID
            include_pending: Include pending approval (DM only)

        Returns:
            List of visible characters
        """
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            return []

        all_characters = self._character_repo.get_by_game_id(game_id)

        # DM can see all characters
        if membership.role_in_game == GameRoleInGame.DM:
            if include_pending:
                return all_characters
            return [c for c in all_characters if c.status != CharacterStatus.DRAFT]

        # Players see their own + approved characters
        return [
            c for c in all_characters
            if c.user_id == user_id or c.status == CharacterStatus.APPROVED
        ]

    def get_pending_characters(self, game_id: int, dm_user_id: int) -> list[Character]:
        """
        Get characters pending approval (DM only).

        Args:
            game_id: The game ID
            dm_user_id: The DM user ID

        Returns:
            List of characters pending approval

        Raises:
            ValueError: If user is not the DM
        """
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, dm_user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise ValueError("Only the DM can view pending characters")

        return self._character_repo.get_pending_approval(game_id)

