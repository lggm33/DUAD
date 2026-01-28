from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, joinedload

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
        Eager loads invites to avoid N+1 queries.
        """
        return (
            self._session.query(Game)
            .options(joinedload(Game.invites))
            .all()
        )

    def get_games_by_ids(self, game_ids: list[int]) -> list[Game]:
        """
        Get games by a list of IDs.
        """
        if not game_ids:
            return []
        return self._session.query(Game).filter(Game.id.in_(game_ids)).all()

    def get_games_with_filters_admin(
        self,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> list[Game]:
        """
        Get all games with optional filters for admin.
        """
        from app.domain.games.models import GameMembership
        
        query = self._session.query(Game).options(
            joinedload(Game.dm_user),
            joinedload(Game.memberships).joinedload(GameMembership.user),
            joinedload(Game.invites)
        )
        
        if status:
            query = query.filter(Game.status == status)
            
        if user_id:
            query = query.join(Game.memberships).filter(GameMembership.user_id == user_id)
            
        if search:
            query = query.filter(Game.name.ilike(f"%{search}%"))
            
        return query.order_by(Game.created_at.desc()).all()
