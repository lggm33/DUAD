"""
Service for Character business logic.

Handles character creation, validation, approval workflow,
and conversion to NPC.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from app.domain.characters.models import Character, CharacterStatus
from app.domain.characters.character_repository import CharacterRepository
from app.domain.characters.exceptions import (
    CharacterNotFoundError,
    CharacterAccessDeniedError,
    CharacterNotEditableError,
)
from app.domain.games.models import Game
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameMembershipStatus, GameRoleInGame
from app.domain.users.user_repository import UserRepository


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
        user_repository: UserRepository,
        event_emitter: Any,
    ) -> None:
        self._character_repo = character_repository
        self._game_repo = game_repository
        self._membership_repo = game_membership_repository
        self._user_repo = user_repository
        self._event_emitter = event_emitter

    def create_character(
        self,
        game_id: int,
        user_id: int,
        name: str,
        data: dict[str, Any],
        submit_for_approval: bool = False,
    ) -> Character:
        """
        Create a new character for a player in a game.

        Args:
            game_id: The game ID
            user_id: The user creating the character
            name: Character name
            data: Character data (class, race, stats, etc.)
            submit_for_approval: If True, submit for DM approval immediately

        Returns:
            The created character

        Raises:
            CharacterNotFoundError: If game not found
            ValueError: If user already has a character in this game
            ValueError: If user is not a member of the game
        """
        game = self._game_repo.get_game_by_id(game_id)
        if not game:
            raise CharacterNotFoundError("Game not found")

        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise ValueError("User is not an active member of this game")

        existing = self._character_repo.get_by_game_and_user(game_id, user_id)
        if existing:
            raise ValueError("User already has a character in this game")

        status = CharacterStatus.DRAFT
        if submit_for_approval:
            if game.requires_character_approval():
                status = CharacterStatus.PENDING_APPROVAL
            else:
                status = CharacterStatus.APPROVED

        character = Character(
            game_id=game_id,
            user_id=user_id,
            name=name,
            status=status,
            data=data,
        )

        character = self._character_repo.create(character)

        # Emit event if submitted for approval
        if status == CharacterStatus.PENDING_APPROVAL:
            user = self._user_repo.get_by_id(user_id)
            player_name = user.username if user else "Unknown"
            self._event_emitter.emit_character_submitted(
                game_id=game_id,
                character_id=character.id,
                character_name=character.name,
                player_name=player_name,
                user_id=user_id,
            )

        return character

    def update_character(
        self,
        character_id: int,
        user_id: int,
        name: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
        submit_for_approval: bool = False,
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
            submit_for_approval: If True, submit for DM approval after update

        Returns:
            The updated character

        Raises:
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If not owned by user
            CharacterNotEditableError: If not editable
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        if character.user_id != user_id:
            raise CharacterAccessDeniedError("You can only update your own character")

        if not character.is_editable():
            raise CharacterNotEditableError(
                f"Character cannot be edited in status: {character.status.value}"
            )

        if name is not None:
            character.name = name
        if data is not None:
            character.data = data

        # Clear any previous rejection feedback when player updates
        if character.status == CharacterStatus.REJECTED:
            character.dm_feedback = None

        # Handle submit for approval
        if submit_for_approval:
            game = self._game_repo.get_game_by_id(character.game_id)
            if game and game.requires_character_approval():
                character.status = CharacterStatus.PENDING_APPROVAL
            else:
                character.status = CharacterStatus.APPROVED
        else:
            # If not submitting, keep as draft
            if character.status == CharacterStatus.REJECTED:
                character.status = CharacterStatus.DRAFT

        # Emit event if submitted for approval
        if submit_for_approval and character.status == CharacterStatus.PENDING_APPROVAL:
            user = self._user_repo.get_by_id(user_id)
            player_name = user.username if user else "Unknown"
            self._event_emitter.emit_character_submitted(
                game_id=character.game_id,
                character_id=character.id,
                character_name=character.name,
                player_name=player_name,
                user_id=user_id,
            )

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
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If not authorized
            ValueError: If character not pending
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        # Verify the user is the DM of this game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            character.game_id, dm_user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise CharacterAccessDeniedError("Only the DM can approve characters")

        if character.status != CharacterStatus.PENDING_APPROVAL:
            raise ValueError("Character is not pending approval")

        character.status = CharacterStatus.APPROVED
        character.dm_feedback = feedback

        # Emit event
        self._event_emitter.emit_character_approved(
            game_id=character.game_id,
            character_id=character.id,
            character_name=character.name,
            user_id=character.user_id,
            feedback=feedback,
        )

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
            CharacterNotFoundError: If character not found
            CharacterAccessDeniedError: If not authorized
            ValueError: If character not pending or feedback missing
        """
        character = self._character_repo.get_by_id(character_id)

        if not character:
            raise CharacterNotFoundError("Character not found")

        if not feedback or not feedback.strip():
            raise ValueError("Feedback is required when rejecting a character")

        # Verify the user is the DM of this game
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            character.game_id, dm_user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise CharacterAccessDeniedError("Only the DM can reject characters")

        if character.status != CharacterStatus.PENDING_APPROVAL:
            raise ValueError("Character is not pending approval")

        character.status = CharacterStatus.REJECTED
        character.dm_feedback = feedback.strip()

        # Emit event
        self._event_emitter.emit_character_rejected(
            game_id=character.game_id,
            character_id=character.id,
            character_name=character.name,
            user_id=character.user_id,
            feedback=feedback,
        )

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

    def get_user_approved_character_in_game(
        self,
        game_id: int,
        user_id: int,
    ) -> Optional[Character]:
        """
        Get the user's approved character in a specific game.

        Only returns the character if it exists and has APPROVED status.
        """
        character = self._character_repo.get_by_game_and_user(game_id, user_id)
        if character and character.status == CharacterStatus.APPROVED:
            return character
        return None

    def get_game_characters(
        self,
        game_id: int,
        user_id: int,
        include_pending: bool = False,
        status_filter: Optional[str] = None,
    ) -> list[Character]:
        """
        Get characters in a game visible to the user.

        Args:
            game_id: The game ID
            user_id: The requesting user ID
            include_pending: Include pending approval (DM only)
            status_filter: Filter by character status (optional)

        Returns:
            List of visible characters

        Raises:
            CharacterAccessDeniedError: If user is not an active member of the game
        """
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise CharacterAccessDeniedError("You must be an active member of the game to view characters")

        all_characters = self._character_repo.get_by_game_id(game_id)

        # DM can see all characters
        if membership.role_in_game == GameRoleInGame.DM:
            if include_pending:
                characters = all_characters
            else:
                characters = [c for c in all_characters if c.status != CharacterStatus.DRAFT]
        else:
            # Players see their own + approved characters
            characters = [
                c for c in all_characters
                if c.user_id == user_id or c.status == CharacterStatus.APPROVED
            ]

        # Apply status filter if provided
        if status_filter:
            status_filter_upper = status_filter.upper()
            characters = [c for c in characters if c.status.value == status_filter_upper]

        return characters

    def get_pending_characters(self, game_id: int, dm_user_id: int) -> list[Character]:
        """
        Get characters pending approval (DM only).

        Args:
            game_id: The game ID
            dm_user_id: The DM user ID

        Returns:
            List of characters pending approval

        Raises:
            CharacterAccessDeniedError: If user is not the DM
        """
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, dm_user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise CharacterAccessDeniedError("Only the DM can view pending characters")

        return self._character_repo.get_pending_approval(game_id)

    def verify_character_in_game(self, character_id: int, game_id: int) -> None:
        """
        Verify that a character belongs to a specific game.

        Args:
            character_id: The character ID
            game_id: The game ID

        Raises:
            CharacterNotFoundError: If character not found or doesn't belong to the game
        """
        character = self._character_repo.get_by_id(character_id)
        if not character or character.game_id != game_id:
            raise CharacterNotFoundError("Character not found in this game")

