"""
Presenter for Character entities.

Transforms Character domain objects into API response dictionaries.
"""

from typing import Any

from app.presentation.base import Presenter
from app.domain.characters.models import Character


class CharacterPresenter(Presenter):
    """Presenter for Character entities."""

    @staticmethod
    def public(character: Character) -> dict[str, Any]:
        """
        Returns a public dictionary for a Character.

        Includes full character data for the owner or DM view.
        """
        return {
            "id": character.id,
            "game_id": character.game_id,
            "user_id": character.user_id,
            "name": character.name,
            "status": character.status.value,
            "data": character.data,
            "dm_feedback": character.dm_feedback,
            "is_editable": character.is_editable(),
            "is_playable": character.is_playable(),
            "created_at": character.created_at.isoformat() if character.created_at else None,
            "updated_at": character.updated_at.isoformat() if character.updated_at else None,
        }

    @staticmethod
    def summary(character: Character) -> dict[str, Any]:
        """
        Returns a summary dictionary for a Character.

        Useful for listing characters without full data.
        """
        return {
            "id": character.id,
            "game_id": character.game_id,
            "user_id": character.user_id,
            "name": character.name,
            "status": character.status.value,
            "is_playable": character.is_playable(),
            "created_at": character.created_at.isoformat() if character.created_at else None,
        }

    @staticmethod
    def collection(characters: list[Character]) -> list[dict[str, Any]]:
        """Returns a list of public dictionaries for a collection of Characters."""
        return [CharacterPresenter.public(c) for c in characters]

    @staticmethod
    def summary_collection(characters: list[Character]) -> list[dict[str, Any]]:
        """Returns a list of summary dictionaries for a collection of Characters."""
        return [CharacterPresenter.summary(c) for c in characters]

