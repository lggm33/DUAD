"""
Service for managing RulesetTemplate operations.

Handles validation, creation, and rule merging for ruleset templates.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.domain.games.ruleset_models import RulesetTemplate, RulesetSystemType
from app.domain.games.schemas.validators import (
    get_default_rules,
    get_effective_rules,
    merge_rules,
    validate_base_rules,
    RulesValidationError,
)


class RulesetService:
    """Service for managing RulesetTemplate operations."""

    @staticmethod
    def get_default_rules() -> dict[str, Any]:
        """
        Get default rules as a dictionary.

        Returns:
            Dictionary with all default values from BaseRulesV1
        """
        return get_default_rules()

    @staticmethod
    def set_template_base_rules(
        template: RulesetTemplate,
        rules: dict[str, Any],
    ) -> None:
        """
        Validate and set base_rules for a template.

        Args:
            template: The template to update
            rules: Dictionary containing base rules

        Raises:
            RulesValidationError: If validation fails
        """
        validated = validate_base_rules(rules)
        template.base_rules = validated.model_dump()

    @staticmethod
    def get_template_base_rules_typed(template: RulesetTemplate) -> BaseModel:
        """
        Get base_rules as a validated Pydantic model.

        Args:
            template: The template to get rules from

        Returns:
            Validated Pydantic model (BaseRulesV1 or future versions)

        Raises:
            RulesValidationError: If stored rules are invalid
        """
        return validate_base_rules(template.base_rules)

    @staticmethod
    def get_template_effective_rules(
        template: RulesetTemplate,
        custom_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Merge base rules with custom overrides and return as dict.

        Args:
            template: The template to get base rules from
            custom_overrides: Optional custom rules to merge

        Returns:
            Merged rules as dictionary
        """
        return merge_rules(template.base_rules, custom_overrides)

    @staticmethod
    def get_template_effective_rules_typed(
        template: RulesetTemplate,
        custom_overrides: dict[str, Any] | None = None,
    ) -> BaseModel:
        """
        Merge base rules with custom overrides and return as typed model.

        Args:
            template: The template to get base rules from
            custom_overrides: Optional custom rules to merge

        Returns:
            Validated Pydantic model with merged rules

        Raises:
            RulesValidationError: If merged rules are invalid
        """
        return get_effective_rules(template.base_rules, custom_overrides)

    @staticmethod
    def create_template(
        name: str,
        system_type: RulesetSystemType,
        rules: dict[str, Any] | None = None,
        description: str | None = None,
        created_by_user_id: int | None = None,
        is_system_provided: bool = False,
    ) -> RulesetTemplate:
        """
        Create a new RulesetTemplate with validated rules.

        Args:
            name: Template name
            system_type: Game system type (DND_5E, PATHFINDER_2E, CUSTOM)
            rules: Base rules (uses defaults if None)
            description: Optional description
            created_by_user_id: Creator user ID (None for system templates)
            is_system_provided: Whether this is a system-provided template

        Returns:
            New RulesetTemplate instance with validated rules

        Raises:
            RulesValidationError: If rules validation fails
        """
        # Use default rules if none provided
        base_rules = rules if rules is not None else get_default_rules()

        # Validate rules
        validated = validate_base_rules(base_rules)

        template = RulesetTemplate(
            name=name,
            description=description,
            system_type=system_type,
            base_rules=validated.model_dump(),
            is_system_provided=is_system_provided,
            created_by_user_id=created_by_user_id,
        )

        return template

