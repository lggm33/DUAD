from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, TypedDict

from app.domain.games.models import (
    Game,
    GameInvite,
    GameRoleInGame,
    GameMembership,
    GameMembershipStatus,
    GameStatus,
)

from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
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
    ) -> None:
        self._game_repository = game_repository
        self._game_invites_repository = game_invites_repository
        self._game_membership_repository = game_membership_repository
        self._user_repository = user_repository

    def create_game(self, name: str, dm_user_id: int) -> CreateGameResult:
        """
        Create a new game.
        """

        # Verify DM user exists
        if not self._user_repository.get_by_id(dm_user_id):
            raise ValueError("DM user not found")

        # Verify DM user is not already a DM of another active game
        existing_game = self._game_repository.get_game_by_dm_user_id(dm_user_id)

        if existing_game is not None and existing_game.status == GameStatus.ACTIVE:
            raise ValueError("DM user is already a DM of another active game")

        # Create game
        game = Game(name=name, dm_user_id=dm_user_id, status=GameStatus.ACTIVE)
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
            raise ValueError("Game not found")

        if current_game.status != GameStatus.ACTIVE:
            raise ValueError("Game is not active")

        # Verify user is not already an active member or kicked from the game
        existing_membership = (
            self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
                current_game.id, user_id
            )
        )
        if existing_membership:
            if existing_membership.status == GameMembershipStatus.ACTIVE:
                raise ValueError("User is already an active member of the game")
            if existing_membership.status == GameMembershipStatus.KICKED:
                raise ValueError("User has been kicked from this game")

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
        """
        invite = self._game_invites_repository.get_game_invite_by_code(invite_code)
        if invite is None:
            raise ValueError("Invalid invite code")

        if not invite.is_valid():
            raise ValueError("Invite code is no longer valid")

        membership = self.join_game(invite.game_id, user_id)
        return {"game": invite.game, "membership": membership}

    def leave_game(self, game_id: int, user_id: int) -> bool:
        """
        Leave a game.
        """
        current_game = self._game_repository.get_game_by_id(game_id)
        if current_game is None:
            raise ValueError("Game not found")

        membership = (
            self._game_membership_repository.get_game_membership_by_game_id_and_user_id(
                current_game.id, user_id
            )
        )

        if membership is None or membership.status != GameMembershipStatus.ACTIVE:
            raise ValueError("User is not an active member of the game")

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
            raise ValueError("User to kick is not a member of the game")
        
        if auth_user.role == UserRole.ADMIN.value:
            membership.status = GameMembershipStatus.KICKED
            return True
        
        if auth_user.role == UserRole.USER.value:
            user_membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(game_id, auth_user.user_id)
            if user_membership is None:
                raise ValueError("User is not a member of the game")
            if user_membership.status != GameMembershipStatus.ACTIVE:
                raise ValueError("User is not an active member of the game")
            if user_membership.role_in_game != GameRoleInGame.DM:
                raise ValueError("User is not a DM of the game")
            membership.status = GameMembershipStatus.KICKED
            return True
        raise ValueError("User is not authorized to kick users from this game")
            

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
        Raises ValueError if user doesn't have permission.
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
            raise ValueError("User is not a member of this game")
        
        if membership.status != GameMembershipStatus.ACTIVE:
            raise ValueError("User is not an active member of this game")
        
        return game

    def get_game_members(self, game_id: int, user: AuthUser) -> list[GameMemberInfo]:
        """
        Get all members of a game.
        Returns list of GameMemberInfo with user data.
        Raises ValueError if user doesn't have permission.
        """
        game = self._game_repository.get_game_by_id(game_id)
        
        if game is None:
            raise ValueError("Game not found")
        
        # Verify user has access to view members
        if user.role != UserRole.ADMIN.value:
            membership = self._game_membership_repository.get_game_membership_by_game_id_and_user_id(game_id, user.user_id)
            if membership is None:
                raise ValueError("User is not a member of this game")
            if membership.status != GameMembershipStatus.ACTIVE:
                raise ValueError("User is not an active member of this game")
        
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