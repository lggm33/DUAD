/**
 * Game Creator Constants
 * Default values and options for game creation
 */

export const MODAL_ID = 'game-creator-modal'

export const CUSTOM_TEMPLATE_ID = 3

export const DEFAULT_RULES = {
  character: {
    creation_mode: 'dm_approval',
    level: {
      min: 1,
      max: 20,
      default: 1
    },
    attributes: {
      method: 'point_buy',
      point_buy: {
        total_points: 27,
        min_score: 8,
        max_score: 15
      }
    },
    races: {
      allow_all: true,
      allowed: [],
      banned: []
    },
    classes: {
      allow_all: true,
      allowed: [],
      banned: [],
      allow_multiclass: true
    },
    backstory: {
      required: false
    },
    allow_custom_backgrounds: true
  },
  combat: {
    turn_timeout: {
      enabled: true,
      grace_period_seconds: 60,
      max_wait_seconds: 180,
      default_action: 'dodge'
    },
    disconnection: {
      show_status_to_party: true,
      allow_dm_control: true,
      auto_pause_on_disconnect: false
    },
    flanking_gives_advantage: false,
    critical_hit_rule: 'double_dice'
  }
}

export const ATTRIBUTE_METHODS = [
  { value: 'point_buy', label: 'Point Buy' },
  { value: 'standard_array', label: 'Standard Array' },
  { value: 'roll_4d6_drop_lowest', label: 'Roll 4d6 Drop Lowest' },
  { value: 'manual', label: 'Manual Entry' }
]

export const CREATION_MODES = [
  { value: 'open', label: 'Open (auto-approve)' },
  { value: 'dm_approval', label: 'Requires DM Approval' }
]

export const DEFAULT_ACTIONS = [
  { value: 'dodge', label: 'Dodge' },
  { value: 'nothing', label: 'Do Nothing' },
  { value: 'defend', label: 'Defend' }
]

export const CRITICAL_HIT_RULES = [
  { value: 'double_dice', label: 'Double Dice' },
  { value: 'double_damage', label: 'Double Damage' },
  { value: 'max_plus_roll', label: 'Max + Roll' }
]

export const AVAILABLE_RACES = [
  'Human', 'Elf', 'Dwarf', 'Halfling', 'Dragonborn',
  'Gnome', 'Half-Elf', 'Half-Orc', 'Tiefling', 'Aasimar',
  'Goliath', 'Tabaxi', 'Kenku', 'Firbolg', 'Lizardfolk'
]

export const AVAILABLE_CLASSES = [
  'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
  'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer',
  'Warlock', 'Wizard', 'Artificer', 'Blood Hunter'
]

