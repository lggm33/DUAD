"""
RulesetTemplate model for game rule configurations.

Provides reusable rule templates (D&D 5e, Pathfinder, Custom) that can be
selected when creating a game, with support for custom overrides.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin
from app.domain.games.schemas.validators import (
    get_default_rules,
    get_effective_rules,
    merge_rules,
    RulesValidationError,
    validate_base_rules,
)


if TYPE_CHECKING:
    from app.domain.users.models import User


class RulesetSystemType(str, Enum):
    """Supported game systems."""

    DND_5E = "DND_5E"
    PATHFINDER_2E = "PATHFINDER_2E"
    CUSTOM = "CUSTOM"


class RulesetTemplate(Base, IntPrimaryKeyMixin, TimestampMixin):
    """
    Template for game rules configuration.

    Can be system-provided (D&D 5e, Pathfinder) or user-created custom rulesets.
    Games reference these templates and can override specific rules.

    The base_rules field stores a validated JSON structure following
    the BaseRulesV1 schema (or future versions).
    """

    __tablename__ = "ruleset_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_type: Mapped[RulesetSystemType] = mapped_column(
        SQLEnum(RulesetSystemType, name="ruleset_system_type"),
        nullable=False,
    )
    base_rules: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=get_default_rules,
    )
    is_system_provided: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    created_by_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_ruleset_templates",
    )
    games: Mapped[list["Game"]] = relationship(  # type: ignore  # noqa: F821
        "Game",
        back_populates="ruleset_template",
    )

    def set_base_rules(self, rules: dict[str, Any]) -> None:
        """
        Validate and set base_rules.

        Args:
            rules: Dictionary containing base rules

        Raises:
            RulesValidationError: If validation fails
        """
        validated = validate_base_rules(rules)
        self.base_rules = validated.model_dump()

    def get_base_rules_typed(self) -> BaseModel:
        """
        Get base_rules as a validated Pydantic model.

        Returns:
            Validated Pydantic model (BaseRulesV1 or future versions)

        Raises:
            RulesValidationError: If stored rules are invalid
        """
        return validate_base_rules(self.base_rules)

    def get_effective_rules_dict(
        self,
        custom_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Merge base rules with custom overrides and return as dict.

        Args:
            custom_overrides: Optional custom rules to merge

        Returns:
            Merged rules as dictionary
        """
        return merge_rules(self.base_rules, custom_overrides)

    def get_effective_rules_typed(
        self,
        custom_overrides: dict[str, Any] | None = None,
    ) -> BaseModel:
        """
        Merge base rules with custom overrides and return as typed model.

        Args:
            custom_overrides: Optional custom rules to merge

        Returns:
            Validated Pydantic model with merged rules

        Raises:
            RulesValidationError: If merged rules are invalid
        """
        return get_effective_rules(self.base_rules, custom_overrides)

