"""
Repository for RulesetTemplate persistence.

Handles database operations for ruleset templates.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.games.ruleset_models import RulesetTemplate


class RulesetRepository:
    """Repository for managing RulesetTemplate persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.
        """
        self._session = session

    def create(self, template: RulesetTemplate) -> RulesetTemplate:
        """
        Create a new ruleset template.
        """
        self._session.add(template)
        self._session.flush()
        return template

    def get_by_id(self, template_id: int) -> Optional[RulesetTemplate]:
        """
        Get a ruleset template by its ID.
        """
        return self._session.query(RulesetTemplate).filter_by(id=template_id).first()

    def get_all(self) -> list[RulesetTemplate]:
        """
        Get all ruleset templates.
        """
        return self._session.query(RulesetTemplate).all()

    def get_system_provided(self) -> list[RulesetTemplate]:
        """
        Get all system-provided ruleset templates.
        """
        return (
            self._session.query(RulesetTemplate)
            .filter_by(is_system_provided=True)
            .all()
        )

    def get_by_user_id(self, user_id: int) -> list[RulesetTemplate]:
        """
        Get all ruleset templates created by a specific user.
        """
        return (
            self._session.query(RulesetTemplate)
            .filter_by(created_by_user_id=user_id)
            .all()
        )

    def get_available_for_user(self, user_id: int) -> list[RulesetTemplate]:
        """
        Get all templates available to a user.
        Includes system-provided templates and templates created by the user.
        """
        return (
            self._session.query(RulesetTemplate)
            .filter(
                (RulesetTemplate.is_system_provided == True)
                | (RulesetTemplate.created_by_user_id == user_id)
            )
            .all()
        )

    def delete(self, template: RulesetTemplate) -> None:
        """
        Delete a ruleset template.
        """
        self._session.delete(template)
        self._session.flush()

