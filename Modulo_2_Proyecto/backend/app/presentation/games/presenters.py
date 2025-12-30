from app.presentation.base import Presenter
from app.domain.games.models import Game, GameInvite
from app.domain.games.game_service import CreateGameResult
from typing import Any

class GamePresenter(Presenter):
    """
    Presenter for Game entities.
    """
    
    @staticmethod
    def public(params: CreateGameResult) -> dict[str, Any]:
        """
        Returns a public dictionary for a Game.
        """
        game = params["game"]
        game_invite = params["game_invite"]
        return {
          "game": {
            "name": game.name,
            "status": game.status,
            "dm_user_id": game.dm_user_id,
            "created_at": game.created_at,
            "updated_at": game.updated_at,
          },
          "invite_code": game_invite.code,
          "invite_url": f"/api/v1/game/join/{game_invite.code}",
        }
    
    @staticmethod
    def collection(params: list[CreateGameResult]) -> list[dict[str, Any]]:
        """
        Returns a list of public dictionaries for a collection of Games.
        """
        return [GamePresenter.public(param) for param in params]