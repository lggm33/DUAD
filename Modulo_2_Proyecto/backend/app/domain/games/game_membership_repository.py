from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.games.models import GameMembership

from datetime import datetime


class GameMembershipRepository:
    """Repository for managing game membership persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.
        """
        self._session = session
        
    def create_game_membership(self, game_membership: GameMembership) -> GameMembership:
        """
        Create a new game membership.
        """
        self._session.add(game_membership)
        self._session.flush()
        return game_membership

    def get_game_membership_by_id(self, game_membership_id: int) -> Optional[GameMembership]:
        """
        Get a game membership by its ID.
        """
        return self._session.query(GameMembership).filter_by(id=game_membership_id).first()

    def get_game_memberships_by_game_id(self, game_id: int) -> list[GameMembership]:
        """
        Get all game memberships by game ID.
        """
        return self._session.query(GameMembership).filter_by(game_id=game_id).all()

    def get_game_memberships_by_user_id(self, user_id: int) -> list[GameMembership]:
        """
        Get all game memberships by user ID.
        """
        return self._session.query(GameMembership).filter_by(user_id=user_id).all()

    def get_game_membership_by_game_id_and_user_id(self, game_id: int, user_id: int) -> Optional[GameMembership]:
        """
        Get a game membership by game ID and user ID.
        """
        return self._session.query(GameMembership).filter_by(game_id=game_id, user_id=user_id).first()
