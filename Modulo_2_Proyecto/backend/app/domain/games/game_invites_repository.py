from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.games.models import GameInvite


class GameInvitesRepository:
    """Repository for managing game invites persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.
        """
        self._session = session

    def create_game_invite(self, game_invite: GameInvite) -> GameInvite:
        """
        Create a new game invite.
        """
        self._session.add(game_invite)
        self._session.flush()
        return game_invite

    def get_game_invite_by_id(self, game_invite_id: int) -> Optional[GameInvite]:
        """
        Get a game invite by its ID.
        """
        return self._session.query(GameInvite).filter_by(id=game_invite_id).first()

    def get_game_invites_by_game_id(self, game_id: int) -> list[GameInvite]:
        """
        Get all game invites by game ID.
        """
        return self._session.query(GameInvite).filter_by(game_id=game_id).all()

    def get_game_invites_by_created_by_user_id(self, created_by_user_id: int) -> list[GameInvite]:
        """
        Get all game invites by created by user ID.
        """
        return self._session.query(GameInvite).filter_by(created_by_user_id=created_by_user_id).all()