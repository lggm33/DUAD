/**
 * Character Creator Constants
 * 
 * Static configuration and default values for character creation
 */

export const MODAL_ID = 'character-creator-modal'

export const STAT_NAMES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']

export const STAT_FULL_NAMES = {
  STR: 'Strength',
  DEX: 'Dexterity',
  CON: 'Constitution',
  INT: 'Intelligence',
  WIS: 'Wisdom',
  CHA: 'Charisma'
}

export const DEFAULT_SKILLS = [
  { name: 'Acrobatics', stat: 'DEX' },
  { name: 'Animal Handling', stat: 'WIS' },
  { name: 'Arcana', stat: 'INT' },
  { name: 'Athletics', stat: 'STR' },
  { name: 'Deception', stat: 'CHA' },
  { name: 'History', stat: 'INT' },
  { name: 'Insight', stat: 'WIS' },
  { name: 'Intimidation', stat: 'CHA' },
  { name: 'Investigation', stat: 'INT' },
  { name: 'Medicine', stat: 'WIS' },
  { name: 'Nature', stat: 'INT' },
  { name: 'Perception', stat: 'WIS' },
  { name: 'Performance', stat: 'CHA' },
  { name: 'Persuasion', stat: 'CHA' },
  { name: 'Religion', stat: 'INT' },
  { name: 'Sleight of Hand', stat: 'DEX' },
  { name: 'Stealth', stat: 'DEX' },
  { name: 'Survival', stat: 'WIS' }
]

export const DEFAULT_RACES = [
  'Human', 'Elf', 'Dwarf', 'Halfling', 'Dragonborn',
  'Gnome', 'Half-Elf', 'Half-Orc', 'Tiefling'
]

export const DEFAULT_CLASSES = [
  'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
  'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer',
  'Warlock', 'Wizard'
]

export const POINT_BUY_COSTS = {
  8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9
}

export const DEFAULT_POINT_BUY_TOTAL = 27
export const STAT_MIN = 8
export const STAT_MAX = 15
export const DEFAULT_SKILL_COUNT = 2
