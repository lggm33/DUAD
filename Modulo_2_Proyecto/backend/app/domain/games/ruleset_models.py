"""
RulesetTemplate model for game rule configurations.

Provides reusable rule templates (D&D 5e, Pathfinder, Custom) that can be
selected when creating a game, with support for custom overrides.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


if TYPE_CHECKING:
    from app.domain.users.models import User


class RulesetSystemType(str, Enum):
    """Supported game systems."""

    DND_5E = "DND_5E"
    PATHFINDER_2E = "PATHFINDER_2E"
    CUSTOM = "CUSTOM"


# ID of the Custom template in the database (from seed_templates.py)
# When this template is selected, custom_rules from the frontend are required
# instead of using the template's base_rules directly
CUSTOM_TEMPLATE_ID = 3


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
        default=dict,
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

