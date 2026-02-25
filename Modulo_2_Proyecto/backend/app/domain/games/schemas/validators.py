"""
Validation functions for game rules.

Provides utilities for validating, merging, and managing
game rules with proper versioning support.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from app.domain.games.schemas.base_rules_v1 import BaseRulesV1


# Registry of schema versions
SCHEMA_VERSIONS: dict[str, type[BaseModel]] = {
    "1.0": BaseRulesV1,
}

DEFAULT_VERSION = "1.0"


class RulesValidationError(Exception):
    """Raised when rules validation fails."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []


def validate_base_rules(data: dict[str, Any]) -> BaseModel:
    """
    Validate base_rules JSON and return typed Pydantic model.

    Args:
        data: Dictionary containing base_rules

    Returns:
        Validated Pydantic model (BaseRulesV1 or future versions)

    Raises:
        RulesValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise RulesValidationError("base_rules must be a dictionary")

    version = data.get("version", DEFAULT_VERSION)
    schema_class = SCHEMA_VERSIONS.get(version)

    if not schema_class:
        supported = ", ".join(SCHEMA_VERSIONS.keys())
        raise RulesValidationError(
            f"Unknown schema version: {version}. Supported: {supported}"
        )

    try:
        return schema_class.model_validate(data)
    except ValidationError as e:
        errors = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            }
            for err in e.errors()
        ]
        raise RulesValidationError(
            f"Invalid base_rules: {len(errors)} validation error(s)",
            errors=errors,
        ) from e


def validate_custom_rules(data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Validate custom_rules (partial override of base_rules).

    Custom rules are more lenient - they only need to be valid
    when merged with base rules. This function performs basic
    structure validation.

    Args:
        data: Dictionary containing custom rule overrides

    Returns:
        Validated dictionary (unchanged if valid)

    Raises:
        RulesValidationError: If structure is invalid
    """
    if data is None:
        return {}

    if not isinstance(data, dict):
        raise RulesValidationError("custom_rules must be a dictionary or null")

    # Validate that keys are known sections
    known_sections = {"version", "character", "combat", "npc", "meta"}
    unknown_keys = set(data.keys()) - known_sections

    if unknown_keys:
        raise RulesValidationError(
            f"Unknown sections in custom_rules: {', '.join(unknown_keys)}"
        )

    return data


def get_default_rules() -> dict[str, Any]:
    """
    Get default rules as a dictionary.

    Returns:
        Dictionary with all default values from BaseRulesV1
    """
    return BaseRulesV1().model_dump()


def merge_rules(
    base: dict[str, Any],
    override: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Deep merge base rules with custom overrides.

    Override values take precedence. Nested dicts are merged recursively.
    Lists are replaced entirely (not merged).

    Args:
        base: Base rules dictionary
        override: Custom overrides dictionary (can be None)

    Returns:
        Merged dictionary
    """
    if not override:
        return base.copy() if isinstance(base, dict) else base

    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_rules(result[key], value)
        else:
            result[key] = value

    return result


def get_effective_rules(
    base_rules: dict[str, Any],
    custom_rules: dict[str, Any] | None = None,
) -> BaseModel:
    """
    Get effective rules by merging base with custom and validating.

    Args:
        base_rules: Base rules from template
        custom_rules: Custom overrides from game

    Returns:
        Validated Pydantic model with merged rules

    Raises:
        RulesValidationError: If merged rules are invalid
    """
    merged = merge_rules(base_rules, custom_rules)
    return validate_base_rules(merged)


def rules_to_dict(rules: BaseModel) -> dict[str, Any]:
    """
    Convert validated rules model to dictionary.

    Args:
        rules: Validated Pydantic model

    Returns:
        Dictionary representation
    """
    return rules.model_dump()

