from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.games.models import Game


class GameRepository:
    """Repository for managing game persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.
        """
        self._session = session

    def create_game(self, game: Game) -> Game:
        """
        Create a new game.
        """
        self._session.add(game)
        self._session.flush()
        return game

    def get_game_by_id(self, game_id: int) -> Optional[Game]:
        """
        Get a game by its ID.
        """
        return self._session.query(Game).filter_by(id=game_id).first()

    def get_game_by_dm_user_id(self, dm_user_id: int) -> Optional[Game]:
        """
        Get a game by its DM user ID.
        """
        return self._session.query(Game).filter_by(dm_user_id=dm_user_id).first()

    def get_games(self) -> list[Game]:
        """
        Get all games.
        """
        return self._session.query(Game).all()

    def get_games_by_ids(self, game_ids: list[int]) -> list[Game]:
        """
        Get games by a list of IDs.
        """
        if not game_ids:
            return []
        return self._session.query(Game).filter(Game.id.in_(game_ids)).all()