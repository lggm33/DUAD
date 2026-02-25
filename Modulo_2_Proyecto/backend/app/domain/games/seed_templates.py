"""
Seed script for default RulesetTemplates.

Creates system-provided templates for common game systems.
"""

from sqlalchemy.orm import Session

from app.domain.games.ruleset_models import RulesetTemplate, RulesetSystemType


def get_dnd_5e_rules() -> dict:
    """Get D&D 5th Edition default rules."""
    return {
        "version": "1.0",
        "character": {
            "creation_mode": "dm_approval",
            "level": {"min": 1, "max": 20, "default": 1},
            "attributes": {
                "method": "point_buy",
                "point_buy": {
                    "total_points": 27,
                    "min_score": 8,
                    "max_score": 15,
                    "cost_table": {
                        "8": 0, "9": 1, "10": 2, "11": 3,
                        "12": 4, "13": 5, "14": 7, "15": 9,
                    },
                },
                "standard_array": [15, 14, 13, 12, 10, 8],
                "attributes_list": [
                    {"key": "strength", "name": "Strength", "abbr": "STR"},
                    {"key": "dexterity", "name": "Dexterity", "abbr": "DEX"},
                    {"key": "constitution", "name": "Constitution", "abbr": "CON"},
                    {"key": "intelligence", "name": "Intelligence", "abbr": "INT"},
                    {"key": "wisdom", "name": "Wisdom", "abbr": "WIS"},
                    {"key": "charisma", "name": "Charisma", "abbr": "CHA"},
                ],
            },
            "races": {"allow_all": True, "allowed": [], "banned": []},
            "classes": {
                "allow_all": True,
                "allowed": [],
                "banned": [],
                "allow_multiclass": True,
            },
            "backstory": {"required": False, "min_length": 0, "max_length": 5000},
            "allow_custom_backgrounds": True,
        },
        "combat": {
            "turn_timeout": {
                "enabled": True,
                "grace_period_seconds": 60,
                "max_wait_seconds": 180,
                "default_action": "dodge",
            },
            "disconnection": {
                "show_status_to_party": True,
                "allow_dm_control": True,
                "auto_pause_on_disconnect": False,
            },
            "flanking_gives_advantage": False,
            "critical_hit_rule": "double_dice",
        },
        "npc": {
            "allow_quick_create": True,
            "presets": [
                {"key": "commoner", "name": "Commoner", "hp": 4, "ac": 10, "attack_bonus": "+2", "damage": "1d4"},
                {"key": "guard", "name": "Guard", "hp": 11, "ac": 16, "attack_bonus": "+3", "damage": "1d8+1"},
                {"key": "bandit", "name": "Bandit", "hp": 11, "ac": 12, "attack_bonus": "+3", "damage": "1d6+1"},
                {"key": "goblin", "name": "Goblin", "hp": 7, "ac": 15, "attack_bonus": "+4", "damage": "1d6+2"},
                {"key": "orc", "name": "Orc", "hp": 15, "ac": 13, "attack_bonus": "+5", "damage": "1d12+3"},
            ],
        },
    }


def get_pathfinder_2e_rules() -> dict:
    """Get Pathfinder 2nd Edition default rules."""
    return {
        "version": "1.0",
        "character": {
            "creation_mode": "dm_approval",
            "level": {"min": 1, "max": 20, "default": 1},
            "attributes": {
                "method": "standard_array",
                "point_buy": {
                    "total_points": 25,
                    "min_score": 8,
                    "max_score": 18,
                    "cost_table": {
                        "8": 0, "9": 1, "10": 2, "11": 3,
                        "12": 4, "13": 5, "14": 7, "15": 9,
                        "16": 12, "17": 15, "18": 19,
                    },
                },
                "standard_array": [18, 14, 12, 10, 10, 8],
                "attributes_list": [
                    {"key": "strength", "name": "Strength", "abbr": "STR"},
                    {"key": "dexterity", "name": "Dexterity", "abbr": "DEX"},
                    {"key": "constitution", "name": "Constitution", "abbr": "CON"},
                    {"key": "intelligence", "name": "Intelligence", "abbr": "INT"},
                    {"key": "wisdom", "name": "Wisdom", "abbr": "WIS"},
                    {"key": "charisma", "name": "Charisma", "abbr": "CHA"},
                ],
            },
            "races": {"allow_all": True, "allowed": [], "banned": []},
            "classes": {
                "allow_all": True,
                "allowed": [],
                "banned": [],
                "allow_multiclass": True,
            },
            "backstory": {"required": False, "min_length": 0, "max_length": 5000},
            "allow_custom_backgrounds": True,
        },
        "combat": {
            "turn_timeout": {
                "enabled": True,
                "grace_period_seconds": 90,
                "max_wait_seconds": 240,
                "default_action": "nothing",
            },
            "disconnection": {
                "show_status_to_party": True,
                "allow_dm_control": True,
                "auto_pause_on_disconnect": False,
            },
            "flanking_gives_advantage": True,
            "critical_hit_rule": "double_dice",
        },
        "npc": {
            "allow_quick_create": True,
            "presets": [
                {"key": "commoner", "name": "Commoner", "hp": 4, "ac": 10, "attack_bonus": "+2", "damage": "1d4"},
                {"key": "guard", "name": "Guard", "hp": 15, "ac": 18, "attack_bonus": "+6", "damage": "1d8+2"},
            ],
        },
    }


def get_custom_template_rules() -> dict:
    """Get minimal custom template rules."""
    return {
        "version": "1.0",
        "character": {
            "creation_mode": "open",
            "level": {"min": 1, "max": 20, "default": 1},
            "attributes": {
                "method": "manual",
                "point_buy": {"total_points": 27, "min_score": 3, "max_score": 18},
                "standard_array": [15, 14, 13, 12, 10, 8],
                "attributes_list": [
                    {"key": "strength", "name": "Strength", "abbr": "STR"},
                    {"key": "dexterity", "name": "Dexterity", "abbr": "DEX"},
                    {"key": "constitution", "name": "Constitution", "abbr": "CON"},
                    {"key": "intelligence", "name": "Intelligence", "abbr": "INT"},
                    {"key": "wisdom", "name": "Wisdom", "abbr": "WIS"},
                    {"key": "charisma", "name": "Charisma", "abbr": "CHA"},
                ],
            },
            "races": {"allow_all": True, "allowed": [], "banned": []},
            "classes": {"allow_all": True, "allowed": [], "banned": [], "allow_multiclass": True},
            "backstory": {"required": False, "min_length": 0, "max_length": 10000},
            "allow_custom_backgrounds": True,
        },
        "combat": {
            "turn_timeout": {
                "enabled": False,
                "grace_period_seconds": 60,
                "max_wait_seconds": 180,
                "default_action": "nothing",
            },
            "disconnection": {
                "show_status_to_party": True,
                "allow_dm_control": True,
                "auto_pause_on_disconnect": False,
            },
            "flanking_gives_advantage": False,
            "critical_hit_rule": "double_dice",
        },
        "npc": {"allow_quick_create": True, "presets": []},
    }


SYSTEM_TEMPLATES = [
    {
        "name": "D&D 5th Edition",
        "description": "Standard rules for Dungeons & Dragons 5th Edition. Includes point-buy character creation, standard combat rules, and common NPC presets.",
        "system_type": RulesetSystemType.DND_5E,
        "base_rules": get_dnd_5e_rules(),
    },
    {
        "name": "Pathfinder 2E",
        "description": "Rules for Pathfinder 2nd Edition. Features flexible character creation and tactical combat with flanking rules.",
        "system_type": RulesetSystemType.PATHFINDER_2E,
        "base_rules": get_pathfinder_2e_rules(),
    },
    {
        "name": "Custom System",
        "description": "A blank template for creating your own custom game system. All rules are fully customizable.",
        "system_type": RulesetSystemType.CUSTOM,
        "base_rules": get_custom_template_rules(),
    },
]


def seed_ruleset_templates(session: Session) -> list[RulesetTemplate]:
    """
    Seed the database with default system-provided templates.
    
    Only creates templates that don't already exist (by name).
    
    Args:
        session: Database session
        
    Returns:
        List of created templates
    """
    created = []
    
    for template_data in SYSTEM_TEMPLATES:
        existing = (
            session.query(RulesetTemplate)
            .filter_by(name=template_data["name"], is_system_provided=True)
            .first()
        )
        
        if existing:
            continue
            
        template = RulesetTemplate(
            name=template_data["name"],
            description=template_data["description"],
            system_type=template_data["system_type"],
            base_rules=template_data["base_rules"],
            is_system_provided=True,
            created_by_user_id=None,
        )
        
        session.add(template)
        created.append(template)
    
    if created:
        session.commit()
        
    return created


def run_seed():
    """Run the seed script standalone."""
    from app.extensions import db
    
    session = db.get_session()
    try:
        created = seed_ruleset_templates(session)
        print(f"Created {len(created)} ruleset templates:")
        for template in created:
            print(f"  - {template.name} ({template.system_type.value})")
    finally:
        session.close()

