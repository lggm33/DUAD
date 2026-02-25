"""
Presenters for RulesetTemplate and game rules.
"""

from __future__ import annotations

from typing import Any

from app.presentation.base import Presenter
from app.domain.games.ruleset_models import RulesetTemplate
from app.domain.games.models import Game


class RulesetPresenter(Presenter):
    """
    Presenter for RulesetTemplate and rules-related entities.
    """

    @staticmethod
    def template(template: RulesetTemplate) -> dict[str, Any]:
        """
        Returns a public dictionary for a RulesetTemplate.
        """
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "system_type": template.system_type.value,
            "is_system_provided": template.is_system_provided,
            "created_by_user_id": template.created_by_user_id,
            "created_at": (
                template.created_at.isoformat() if template.created_at else None
            ),
            "updated_at": (
                template.updated_at.isoformat() if template.updated_at else None
            ),
        }

    @staticmethod
    def template_with_rules(template: RulesetTemplate) -> dict[str, Any]:
        """
        Returns a public dictionary for a RulesetTemplate including base_rules.
        """
        return {
            **RulesetPresenter.template(template),
            "base_rules": template.base_rules,
        }

    @staticmethod
    def templates_collection(
        templates: list[RulesetTemplate],
        include_rules: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Returns a list of public dictionaries for a collection of RulesetTemplates.
        
        Args:
            templates: List of RulesetTemplate instances
            include_rules: Whether to include base_rules in the response
        """
        if include_rules:
            return [RulesetPresenter.template_with_rules(t) for t in templates]
        return [RulesetPresenter.template(t) for t in templates]


class GameRulesPresenter(Presenter):
    """
    Presenter for game rules information.
    """

    @staticmethod
    def effective_rules(
        game: Game,
        effective_rules: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Returns game rules information including effective (merged) rules.
        """
        template_info = None
        if game.ruleset_template is not None:
            template_info = {
                "id": game.ruleset_template.id,
                "name": game.ruleset_template.name,
                "system_type": game.ruleset_template.system_type.value,
            }

        return {
            "game_id": game.id,
            "ruleset_template": template_info,
            "custom_rules": game.custom_rules,
            "effective_rules": effective_rules,
            "character_creation_mode": game.character_creation_mode.value,
        }

    @staticmethod
    def rules_summary(game: Game) -> dict[str, Any]:
        """
        Returns a summary of game rules configuration.
        """
        template_info = None
        if game.ruleset_template is not None:
            template_info = {
                "id": game.ruleset_template.id,
                "name": game.ruleset_template.name,
                "system_type": game.ruleset_template.system_type.value,
            }

        return {
            "game_id": game.id,
            "ruleset_template": template_info,
            "has_custom_rules": game.custom_rules is not None,
            "character_creation_mode": game.character_creation_mode.value,
        }

