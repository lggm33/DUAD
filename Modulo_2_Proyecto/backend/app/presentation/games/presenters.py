from app.presentation.base import Presenter
from app.domain.games.models import Game, GameInvite, GameMembership
from app.domain.games.game_service import CreateGameResult, GameWithRole, GameMemberInfo
from typing import Any

class GamePresenter(Presenter):
    """
    Presenter for Game entities.
    """
    
    @staticmethod
    def public(params: CreateGameResult) -> dict[str, Any]:
        """
        Returns a public dictionary for a CreateGameResult (game + invite).
        """
        game = params["game"]
        game_invite = params["game_invite"]
        return {
          "game": GamePresenter.game_only(game),
          "invite_code": game_invite.code,
          "invite_url": f"/api/v1/game/join/{game_invite.code}",
        }
    
    @staticmethod
    def game_only(game: Game) -> dict[str, Any]:
        """
        Returns a public dictionary for a Game entity only.
        """
        return {
            "id": game.id,
            "name": game.name,
            "status": game.status.value if hasattr(game.status, 'value') else game.status,
            "dm_user_id": game.dm_user_id,
            "created_at": game.created_at.isoformat() if game.created_at else None,
            "updated_at": game.updated_at.isoformat() if game.updated_at else None,
        }
    
    @staticmethod
    def game_with_role(game_with_role: GameWithRole) -> dict[str, Any]:
        """
        Returns a public dictionary for a Game with the user's role.
        Includes invite_code only if user is DM.
        """
        game = game_with_role["game"]
        role = game_with_role["role_in_game"]
        membership_status = game_with_role["membership_status"]
        invite_code = game_with_role.get("invite_code")
        
        result = {
            **GamePresenter.game_only(game),
            "role_in_game": role.value if hasattr(role, 'value') else role,
            "membership_status": membership_status.value if hasattr(membership_status, 'value') else membership_status,
        }
        
        if invite_code:
            result["invite_code"] = invite_code
        
        return result

    @staticmethod
    def collection(games: list[GameWithRole]) -> list[dict[str, Any]]:
        """
        Returns a list of public dictionaries for a collection of Games with roles.
        """
        return [GamePresenter.game_with_role(game) for game in games]

    @staticmethod
    def member(member_info: GameMemberInfo) -> dict[str, Any]:
        """
        Returns a public dictionary for a GameMemberInfo.
        """
        membership = member_info["membership"]
        return {
            "id": membership.id,
            "user_id": member_info["user_id"],
            "username": member_info["username"],
            "name": member_info["name"],
            "role_in_game": membership.role_in_game.value if hasattr(membership.role_in_game, 'value') else membership.role_in_game,
            "status": membership.status.value if hasattr(membership.status, 'value') else membership.status,
            "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
            "left_at": membership.left_at.isoformat() if membership.left_at else None,
        }

    @staticmethod
    def members_collection(members: list[GameMemberInfo]) -> list[dict[str, Any]]:
        """
        Returns a list of public dictionaries for a collection of GameMemberInfo.
        """
        return [GamePresenter.member(member) for member in members]