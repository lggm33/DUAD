"""
Service for managing RulesetTemplate operations.

Handles validation, creation, and rule merging for ruleset templates.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.domain.games.ruleset_models import RulesetTemplate, RulesetSystemType
from app.domain.games.ruleset_repository import RulesetRepository
from app.domain.games.exceptions import RulesetNotFoundError, RulesetAccessDeniedError
from app.domain.games.schemas.validators import (
    get_default_rules,
    get_effective_rules,
    merge_rules,
    validate_base_rules,
    RulesValidationError,
)


class RulesetService:
    """Service for managing RulesetTemplate operations."""

    def __init__(self, ruleset_repository: RulesetRepository):
        """
        Initialize RulesetService with required dependencies.

        Args:
            ruleset_repository: Repository for RulesetTemplate persistence
        """
        self._ruleset_repo = ruleset_repository

    def get_available_templates(self, user_id: int) -> list[RulesetTemplate]:
        """
        Get all ruleset templates available to the user.

        Returns system-provided templates and templates created by the user.

        Args:
            user_id: ID of the authenticated user

        Returns:
            List of available RulesetTemplate instances
        """
        return self._ruleset_repo.get_available_for_user(user_id)

    def get_template_by_id(self, template_id: int, user_id: int) -> RulesetTemplate:
        """
        Get a specific ruleset template by ID with access control.

        System templates are publicly accessible.
        User-created templates require ownership.

        Args:
            template_id: ID of the template to retrieve
            user_id: ID of the authenticated user

        Returns:
            RulesetTemplate instance

        Raises:
            RulesetNotFoundError: If template doesn't exist
            RulesetAccessDeniedError: If user doesn't have access to the template
        """
        template = self._ruleset_repo.get_by_id(template_id)

        if template is None:
            raise RulesetNotFoundError(f"Ruleset template with ID {template_id} not found")

        # Check access: system templates are public, user templates require ownership
        if not template.is_system_provided:
            if template.created_by_user_id != user_id:
                raise RulesetAccessDeniedError("You don't have access to this template")

        return template

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

