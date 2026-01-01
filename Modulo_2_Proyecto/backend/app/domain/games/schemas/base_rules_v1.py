"""
Base rules schema version 1.0.

Defines the complete structure for game rules including:
- Character creation rules (level, attributes, races, classes)
- Combat settings (timeouts, disconnection handling)
- NPC templates and presets
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class AttributeMethod(str, Enum):
    """Methods for generating character attributes."""

    POINT_BUY = "point_buy"
    STANDARD_ARRAY = "standard_array"
    ROLL_4D6 = "roll_4d6_drop_lowest"
    MANUAL = "manual"


class CharacterCreationMode(str, Enum):
    """How character creation is handled."""

    OPEN = "open"  # Auto-approved if valid
    DM_APPROVAL = "dm_approval"  # Requires DM approval


class DefaultSkipAction(str, Enum):
    """Default action when turn is skipped."""

    DODGE = "dodge"
    NOTHING = "nothing"
    DEFEND = "defend"


# =============================================================================
# Character Rules
# =============================================================================


class LevelConfig(BaseModel):
    """Configuration for character levels."""

    min: int = Field(default=1, ge=1, le=30, description="Minimum starting level")
    max: int = Field(default=20, ge=1, le=30, description="Maximum allowed level")
    default: int = Field(default=1, ge=1, le=30, description="Default starting level")


class PointBuyConfig(BaseModel):
    """Configuration for point buy attribute generation."""

    total_points: int = Field(default=27, ge=0, le=100)
    min_score: int = Field(default=8, ge=1, le=18)
    max_score: int = Field(default=15, ge=1, le=20)
    cost_table: dict[str, int] = Field(
        default_factory=lambda: {
            "8": 0, "9": 1, "10": 2, "11": 3,
            "12": 4, "13": 5, "14": 7, "15": 9,
        }
    )


class AttributeDefinition(BaseModel):
    """Definition of a single attribute."""

    key: str = Field(description="Unique identifier (e.g., 'strength')")
    name: str = Field(description="Display name (e.g., 'Strength')")
    abbr: str = Field(max_length=5, description="Abbreviation (e.g., 'STR')")


class AttributeConfig(BaseModel):
    """Configuration for character attributes."""

    method: AttributeMethod = Field(default=AttributeMethod.POINT_BUY)
    point_buy: PointBuyConfig = Field(default_factory=PointBuyConfig)
    standard_array: list[int] = Field(default=[15, 14, 13, 12, 10, 8])
    attributes_list: list[AttributeDefinition] = Field(
        default_factory=lambda: [
            AttributeDefinition(key="strength", name="Strength", abbr="STR"),
            AttributeDefinition(key="dexterity", name="Dexterity", abbr="DEX"),
            AttributeDefinition(key="constitution", name="Constitution", abbr="CON"),
            AttributeDefinition(key="intelligence", name="Intelligence", abbr="INT"),
            AttributeDefinition(key="wisdom", name="Wisdom", abbr="WIS"),
            AttributeDefinition(key="charisma", name="Charisma", abbr="CHA"),
        ]
    )


class RaceConfig(BaseModel):
    """Configuration for allowed races."""

    allow_all: bool = Field(default=True, description="Allow all races by default")
    allowed: list[str] = Field(
        default_factory=list,
        description="List of allowed race keys (used when allow_all=False)",
    )
    banned: list[str] = Field(
        default_factory=list,
        description="List of banned race keys (always blocked)",
    )


class ClassConfig(BaseModel):
    """Configuration for allowed classes."""

    allow_all: bool = Field(default=True, description="Allow all classes by default")
    allowed: list[str] = Field(
        default_factory=list,
        description="List of allowed class keys (used when allow_all=False)",
    )
    banned: list[str] = Field(
        default_factory=list,
        description="List of banned class keys (always blocked)",
    )
    allow_multiclass: bool = Field(default=True, description="Allow multiclassing")


class BackstoryConfig(BaseModel):
    """Configuration for character backstory requirements."""

    required: bool = Field(default=False)
    min_length: int = Field(default=0, ge=0, le=10000)
    max_length: int = Field(default=5000, ge=0, le=50000)


class CharacterRules(BaseModel):
    """Complete character creation rules."""

    creation_mode: CharacterCreationMode = Field(default=CharacterCreationMode.OPEN)
    level: LevelConfig = Field(default_factory=LevelConfig)
    attributes: AttributeConfig = Field(default_factory=AttributeConfig)
    races: RaceConfig = Field(default_factory=RaceConfig)
    classes: ClassConfig = Field(default_factory=ClassConfig)
    backstory: BackstoryConfig = Field(default_factory=BackstoryConfig)
    allow_custom_backgrounds: bool = Field(default=True)


# =============================================================================
# Combat Settings
# =============================================================================


class TurnTimeoutConfig(BaseModel):
    """Configuration for turn timeouts during combat."""

    enabled: bool = Field(default=True, description="Enable turn timeouts")
    grace_period_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Grace period before timeout warning",
    )
    max_wait_seconds: int = Field(
        default=180,
        ge=30,
        le=600,
        description="Maximum wait time before DM intervention",
    )
    default_action: DefaultSkipAction = Field(
        default=DefaultSkipAction.DODGE,
        description="Default action when turn is skipped",
    )


class DisconnectionConfig(BaseModel):
    """Configuration for handling player disconnections."""

    show_status_to_party: bool = Field(
        default=True,
        description="Show disconnection status to other players",
    )
    allow_dm_control: bool = Field(
        default=True,
        description="Allow DM to control disconnected player's character",
    )
    auto_pause_on_disconnect: bool = Field(
        default=False,
        description="Automatically pause combat when a player disconnects",
    )


class CombatSettings(BaseModel):
    """Combat-related settings."""

    turn_timeout: TurnTimeoutConfig = Field(default_factory=TurnTimeoutConfig)
    disconnection: DisconnectionConfig = Field(default_factory=DisconnectionConfig)
    flanking_gives_advantage: bool = Field(default=False)
    critical_hit_rule: str = Field(default="double_dice")


# =============================================================================
# NPC Rules
# =============================================================================


class NPCPreset(BaseModel):
    """Preset for quick NPC creation."""

    key: str
    name: str
    hp: int = Field(ge=1)
    ac: int = Field(ge=1, le=30)
    attack_bonus: str = Field(description="e.g., '+3'")
    damage: str = Field(description="e.g., '1d6+1'")


class NPCRules(BaseModel):
    """Rules for NPC creation."""

    allow_quick_create: bool = Field(default=True)
    presets: list[NPCPreset] = Field(
        default_factory=lambda: [
            NPCPreset(key="commoner", name="Commoner", hp=4, ac=10, attack_bonus="+2", damage="1d4"),
            NPCPreset(key="guard", name="Guard", hp=11, ac=16, attack_bonus="+3", damage="1d8+1"),
            NPCPreset(key="bandit", name="Bandit", hp=11, ac=12, attack_bonus="+3", damage="1d6+1"),
        ]
    )


# =============================================================================
# Main Schema
# =============================================================================


class BaseRulesV1(BaseModel):
    """
    Complete base rules schema version 1.0.

    This schema defines all configurable game rules that can be set
    by a DM when creating a game or using a ruleset template.
    """

    version: Literal["1.0"] = Field(
        default="1.0",
        description="Schema version for compatibility checking",
    )
    character: CharacterRules = Field(default_factory=CharacterRules)
    combat: CombatSettings = Field(default_factory=CombatSettings)
    npc: NPCRules = Field(default_factory=NPCRules)

    model_config = {
        "extra": "forbid",  # Reject unknown fields
        "json_schema_extra": {
            "title": "Base Rules Schema v1.0",
            "description": "Schema for RPG game rules configuration",
        },
    }

