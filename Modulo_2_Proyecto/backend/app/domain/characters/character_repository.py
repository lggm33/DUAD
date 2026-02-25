"""
Repository for Character persistence operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.characters.models import Character, CharacterStatus


class CharacterRepository:
    """Repository for managing character persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, character: Character) -> Character:
        """Create a new character."""
        self._session.add(character)
        self._session.flush()
        return character

    def get_by_id(self, character_id: int) -> Optional[Character]:
        """Get a character by ID."""
        return self._session.query(Character).filter_by(id=character_id).first()

    def get_by_game_and_user(
        self,
        game_id: int,
        user_id: int,
    ) -> Optional[Character]:
        """Get a character by game and user (a user has one character per game)."""
        return (
            self._session.query(Character)
            .filter_by(game_id=game_id, user_id=user_id)
            .first()
        )

    def get_by_game_id(self, game_id: int) -> list[Character]:
        """Get all characters in a game."""
        return self._session.query(Character).filter_by(game_id=game_id).all()

    def get_by_user_id(self, user_id: int) -> list[Character]:
        """Get all characters owned by a user."""
        return self._session.query(Character).filter_by(user_id=user_id).all()

    def get_pending_approval(self, game_id: int) -> list[Character]:
        """Get all characters pending DM approval in a game."""
        return (
            self._session.query(Character)
            .filter_by(game_id=game_id, status=CharacterStatus.PENDING_APPROVAL)
            .all()
        )

    def get_approved_by_game(self, game_id: int) -> list[Character]:
        """Get all approved characters in a game."""
        return (
            self._session.query(Character)
            .filter_by(game_id=game_id, status=CharacterStatus.APPROVED)
            .all()
        )

    def delete(self, character: Character) -> None:
        """Delete a character."""
        self._session.delete(character)
        self._session.flush()

