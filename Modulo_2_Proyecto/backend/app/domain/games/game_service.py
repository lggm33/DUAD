from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, TypedDict

from pydantic import BaseModel

from app.domain.games.models import (
    CharacterCreationMode,
    Game,
    GameInvite,
    GameRoleInGame,
    GameMembership,
    GameMembershipStatus,
    GameStatus,
)
from app.domain.games.ruleset_models import CUSTOM_TEMPLATE_ID, RulesetSystemType, RulesetTemplate
from app.domain.games.schemas.validators import (
    get_effective_rules,
    merge_rules,
    validate_base_rules,
    validate_custom_rules,
    RulesValidationError,
)

from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.ruleset_repository import RulesetRepository
from app.domain.games.exceptions import (
    GameNotFoundError,
    GameAccessDeniedError,
    GameValidationError,
    GameStateError,
    GameInviteError,
    GameMembershipError,
    RulesetNotFoundError,
    RulesetAccessDeniedError,
)
from app.domain.users.user_repository import UserRepository
from app.domain.auth.models import AuthUser
from app.domain.users.models import UserRole

class CreateGameResult(TypedDict):
    game: Game
    game_invite: GameInvite


class GameWithRole(TypedDict):
    game: Game
    role_in_game: GameRoleInGame
    membership_status: GameMembershipStatus
    invite_code: Optional[str]


class GameMemberInfo(TypedDict):
    membership: GameMembership
    user_id: int
    username: Optional[str]
    name: str


class GameService:
    """Service for managing game use cases."""

    def __init__(
        self,
        game_repository: GameRepository,
        game_invites_repository: GameInvitesRepository,
        game_membership_repository: GameMembershipRepository,
        user_repository: UserRepository,
        ruleset_repository: RulesetRepository,
    ) -> None:
        self._game_repository = game_repository
        self._game_invites_repository = game_invites_repository
        self._game_membership_repository = game_membership_repository
        self._user_repository = user_repository
        self._ruleset_repository = ruleset_repository

    def create_game(
        self,
        name: str,
        dm_user_id: int,
        ruleset_template_id: int | None = None,
        custom_rules: dict[str, Any] | None = None,
    ) -> CreateGameResult:
        """
        Create a new game with optional ruleset configuration.
        
        Args:
            name: Name of the game
            dm_user_id: ID of the user who will be the DM
            ruleset_template_id: ID of the ruleset template to use
            custom_rules: Optional custom rules to override template defaults
        """

        # Verify DM user exists
        if not self._user_repository.get_by_id(dm_user_id):
            raise GameValidationError("DM user not found")

        # Verify DM user is not already a DM of another active game
        # existing_game = self._game_repository.get_game_by_dm_user_id(dm_user_id)

        # if existing_game is not None and existing_game.status == GameStatus.ACTIVE:
        #     raise ValueError("DM user is already a DM of another active game")

        # Validate ruleset template if provided

        if ruleset_template_id is None:
            raise GameValidationError("Ruleset template ID is required")

        template = self._ruleset_repository.get_by_id(ruleset_template_id)
        
        if template is None:
            raise RulesetNotFoundError("Ruleset template not found")
        
        # Check access: system templates are public, user templates require ownership
        if not template.is_system_provided:
            if template.created_by_user_id != dm_user_id:
                raise RulesetAccessDeniedError("You don't have access to this template")

        # Handle custom template logic
        final_template_id = ruleset_template_id
        
        if ruleset_template_id == CUSTOM_TEMPLATE_ID:
            # Custom template requires custom_rules from the user
            if not custom_rules:
                raise GameValidationError("Custom rules are required when using the Custom template")
            
            validated_rules = validate_custom_rules(custom_rules)
            
            # Create a new user-owned template with the custom rules
            user_template = RulesetTemplate(
                name=f"{name} - Custom Rules",
                description=f"Custom ruleset created for game: {name}",
                system_type=RulesetSystemType.CUSTOM,
                base_rules=validated_rules,
                is_system_provided=False,
                created_by_user_id=dm_user_id,
            )
            created_template = self._ruleset_repository.create(user_template)
            final_template_id = created_template.id
        
        # For other templates, use the template's base_rules directly

        # Determine character creation mode from rules
        character_creation_mode = CharacterCreationMode.OPEN  # Default
        
        # Check custom_rules first (takes priority)
        if custom_rules:
            creation_mode_str = custom_rules.get("character", {}).get("creation_mode", "")
            if creation_mode_str == "dm_approval":
                character_creation_mode = CharacterCreationMode.DM_APPROVAL
        elif template and template.base_rules:
            # Otherwise check template base_rules
            creation_mode_str = template.base_rules.get("character", {}).get("creation_mode", "")
            if creation_mode_str == "dm_approval":
                character_creation_mode = CharacterCreationMode.DM_APPROVAL

        # Create game with ruleset configuration
        game = Game(
            name=name,
            dm_user_id=dm_user_id,
            status=GameStatus.ACTIVE,
            ruleset_template_id=final_template_id,
            custom_rules=None,
            character_creation_mode=character_creation_mode,
        )
        new_game = self._game_repository.create_game(game)

        # Create game membership for DM user
        game_membership = GameMembership(
            game_id=new_game.id,
            user_id=dm_user_id,
            role_in_game=GameRoleInGame.DM,
            status=GameMembershipStatus.ACTIVE,
        )
        self._game_membership_repository.create_game_membership(game_membership)

        # Create game invite for DM user (as creator)
        import secrets

        invite_code = secrets.token_urlsafe(12)
        game_invite = GameInvite(
            game_id=new_game.id,
            code=invite_code,
            created_by_user_id=dm_user_id,
            is_active=True,
        )
        self._game_invites_repository.create_game_invite(game_invite)

        return CreateGameResult(game=new_game, game_invite=game_invite)

    def join_game(self, game_id: int, user_id: int) -> GameMembership:
        """
        Join a game as a player.
        """

        current_game = self._game_repository.get_game_by_id(game_id)
        if current_game is None:
            raise GameNotFoundError("Game not found")

        if current_game.status != GameStatus.ACTIVE:
            raise GameStateError("Game is not active")

        # Verify user is not already an active member or kicked from the game
        existing_membership = (
            self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
                current_game.id, user_id
            )
        )
        if existing_membership:
            if existing_membership.status == GameMembershipStatus.ACTIVE:
                raise GameMembershipError("User is already an active member of the game")
            if existing_membership.status == GameMembershipStatus.KICKED:
                raise GameAccessDeniedError("User has been kicked from this game")

        # Reactivate membership if user previously left
        if existing_membership and existing_membership.status == GameMembershipStatus.LEFT:
            existing_membership.status = GameMembershipStatus.ACTIVE
            existing_membership.left_at = None
            existing_membership.role_in_game = GameRoleInGame.PLAYER
            # SQLAlchemy tracks changes automatically
            return existing_membership

        game_membership = GameMembership(
            game_id=game_id,
            user_id=user_id,
            role_in_game=GameRoleInGame.PLAYER,
            status=GameMembershipStatus.ACTIVE,
        )
        return self._game_membership_repository.create_game_membership(game_membership)

    def join_game_by_code(self, invite_code: str, user_id: int) -> dict[str, Any]:
        """
        Join a game using an invite code.
        Returns both the game and the membership.
        
        If user is already an active member, returns existing membership.
        """
        invite = self._game_invites_repository.get_game_invite_by_code(invite_code)
        if invite is None:
            raise GameInviteError("Invalid invite code")

        if not invite.is_valid():
            raise GameInviteError("Invite code is no longer valid")

        existing_membership = (
            self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
                invite.game_id, user_id
            )
        )
        
        if existing_membership and existing_membership.status == GameMembershipStatus.ACTIVE:
            return {"game": invite.game, "membership": existing_membership}

        membership = self.join_game(invite.game_id, user_id)
        return {"game": invite.game, "membership": membership}

    def leave_game(self, game_id: int, user_id: int) -> bool:
        """
        Leave a game.
        """
        current_game = self._game_repository.get_game_by_id(game_id)
        if current_game is None:
            raise GameNotFoundError("Game not found")

        membership = (
            self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
                current_game.id, user_id
            )
        )

        if membership is None or membership.status != GameMembershipStatus.ACTIVE:
            raise GameMembershipError("User is not an active member of the game")

        # Update game membership status to LEFT
        membership.status = GameMembershipStatus.LEFT
        membership.left_at = datetime.now(timezone.utc)

        if membership.role_in_game == GameRoleInGame.DM:
            current_game.status = GameStatus.ENDED

        return True
        
    def kick_user_from_game(self, game_id: int, user_id: int, auth_user: AuthUser) -> bool:
        """
        Kick a user from a game.
        """
        membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(game_id, user_id)
        if membership is None:
            raise GameMembershipError("User to kick is not a member of the game")
        
        if auth_user.role == UserRole.ADMIN.value:
            membership.status = GameMembershipStatus.KICKED
            return True
        
        if auth_user.role == UserRole.USER.value:
            user_membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(game_id, auth_user.user_id)
            if user_membership is None:
                raise GameMembershipError("User is not a member of the game")
            if user_membership.status != GameMembershipStatus.ACTIVE:
                raise GameMembershipError("User is not an active member of the game")
            if user_membership.role_in_game != GameRoleInGame.DM:
                raise GameAccessDeniedError("Only the DM can kick users from the game")
            membership.status = GameMembershipStatus.KICKED
            return True
        raise GameAccessDeniedError("User is not authorized to kick users from this game")
            

    def get_games(self, user: AuthUser) -> list[GameWithRole]:
        """
        Get games based on user role.
        ADMIN can see all games (with DM role since they have full access).
        Regular users can only see games they are or were members of.
        Returns games with the user's role in each game.
        Includes invite_code only for DM users.
        """
        if user.role == UserRole.ADMIN.value:
            games = self._game_repository.get_games()
            if not games:
                return []
            return [
                GameWithRole(
                    game=game,
                    role_in_game=GameRoleInGame.DM,
                    membership_status=GameMembershipStatus.ACTIVE,
                    invite_code=self._get_active_invite_code(game),
                )
                for game in games
            ]

        memberships = self._game_membership_repository.get_game_memberships_by_user_id(user.user_id)
        if not memberships:
            return []

        return [
            GameWithRole(
                game=membership.game,
                role_in_game=membership.role_in_game,
                membership_status=membership.status,
                invite_code=self._get_active_invite_code(membership.game) if membership.role_in_game == GameRoleInGame.DM else None,
            )
            for membership in memberships
        ]

    def _get_active_invite_code(self, game: Game) -> Optional[str]:
        """
        Get the active invite code for a game.
        Returns None if no active invite exists.
        """
        active_invite = next(
            (invite for invite in game.invites if invite.is_active),
            None
        )
        return active_invite.code if active_invite else None

    def get_game_by_id(self, game_id: int, user: AuthUser) -> Optional[Game]:
        """
        Get a game by its ID.
        Returns None if game not found.
        Raises GameAccessDeniedError if user doesn't have permission.
        """
        game = self._game_repository.get_game_by_id(game_id)

        if game is None:
            return None
        
        # ADMIN can see any game
        if user.role == UserRole.ADMIN.value:
            return game
        
        # Other users can only see games they are active members of
        membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(game_id, user.user_id)
        if membership is None:
            raise GameAccessDeniedError("User is not a member of this game")
        
        if membership.status != GameMembershipStatus.ACTIVE:
            raise GameAccessDeniedError("User is not an active member of this game")
        
        return game

    def get_game_members(self, game_id: int, user: AuthUser) -> list[GameMemberInfo]:
        """
        Get all members of a game.
        Returns list of GameMemberInfo with user data.
        Raises GameNotFoundError if game not found.
        Raises GameAccessDeniedError if user doesn't have permission.
        """
        game = self._game_repository.get_game_by_id(game_id)
        
        if game is None:
            raise GameNotFoundError("Game not found")
        
        # Verify user has access to view members
        if user.role != UserRole.ADMIN.value:
            membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(game_id, user.user_id)
            if membership is None:
                raise GameAccessDeniedError("User is not a member of this game")
            if membership.status != GameMembershipStatus.ACTIVE:
                raise GameAccessDeniedError("User is not an active member of this game")
        
        memberships = self._game_membership_repository.get_game_memberships_by_game_id(game_id)
        
        user_ids = [m.user_id for m in memberships]
        users = self._user_repository.get_users_by_ids(user_ids)
        users_map = {u.id: u for u in users}
        
        return [
            GameMemberInfo(
                membership=m,
                user_id=m.user_id,
                username=users_map[m.user_id].username if m.user_id in users_map else None,
                name=users_map[m.user_id].name if m.user_id in users_map else "Unknown",
            )
            for m in memberships
        ]

    # =========================================================================
    # Rules Management
    # =========================================================================

    def verify_dm_permissions(self, game: Game, user: AuthUser) -> None:
        """
        Verify that the user has DM permissions for the game.
        
        Args:
            game: The game to check permissions for
            user: The authenticated user
            
        Raises:
            GameAccessDeniedError: If user is not DM or ADMIN
        """
        # ADMIN always has permission
        if user.role == UserRole.ADMIN.value:
            return
        
        # Check if user is the DM
        if game.dm_user_id == user.user_id:
            return
        
        # Additional check via membership
        membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
            game.id, user.user_id
        )
        
        if membership is None or membership.role_in_game != GameRoleInGame.DM:
            raise GameAccessDeniedError("Only the DM can perform this operation")

    def set_game_custom_rules(self, game: Game, rules: dict[str, Any] | None) -> None:
        """
        Validate and set custom_rules for a game.

        Args:
            game: The game to update
            rules: Custom rules to override template (can be None to clear)

        Raises:
            RulesValidationError: If validation fails
        """
        validated = validate_custom_rules(rules)
        game.custom_rules = validated if validated else None

    def get_game_effective_rules(self, game: Game) -> dict[str, Any]:
        """
        Get effective rules by merging template with custom rules.

        Args:
            game: The game to get rules for

        Returns:
            Merged rules as dictionary. If no template, returns custom_rules or empty dict.
        """
        if game.ruleset_template is None:
            return game.custom_rules or {}

        return merge_rules(
            game.ruleset_template.base_rules,
            game.custom_rules,
        )

    def get_game_effective_rules_typed(self, game: Game) -> BaseModel:
        """
        Get effective rules as validated Pydantic model.

        Args:
            game: The game to get rules for

        Returns:
            Validated Pydantic model with merged rules.

        Raises:
            RulesValidationError: If no rules configured or validation fails.
        """
        if game.ruleset_template is None:
            if not game.custom_rules:
                raise RulesValidationError("No rules configured for this game")
            # If only custom_rules, they must be complete
            return validate_base_rules(game.custom_rules)

        return get_effective_rules(
            game.ruleset_template.base_rules,
            game.custom_rules,
        )