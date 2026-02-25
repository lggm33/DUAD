"""
Pydantic schemas for game rules validation.

Provides versioned schemas for base_rules JSON structure,
ensuring type safety and validation.
"""

from app.domain.games.schemas.base_rules_v1 import BaseRulesV1
from app.domain.games.schemas.validators import (
    get_default_rules,
    get_effective_rules,
    merge_rules,
    RulesValidationError,
    rules_to_dict,
    validate_base_rules,
    validate_custom_rules,
)

__all__ = [
    "BaseRulesV1",
    "get_default_rules",
    "get_effective_rules",
    "merge_rules",
    "RulesValidationError",
    "rules_to_dict",
    "validate_base_rules",
    "validate_custom_rules",
]

