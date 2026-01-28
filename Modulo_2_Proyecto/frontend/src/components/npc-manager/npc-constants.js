/**
 * NPCManager Constants
 * 
 * Configuration and constants for NPC management system.
 */

export const MODAL_ID = 'npc-manager-modal'
export const FORM_MODAL_ID = 'npc-form-modal'

export const NPC_TYPES = {
  ALLY: { label: 'Ally', class: 'npc-type-ally', icon: '🤝' },
  ENEMY: { label: 'Enemy', class: 'npc-type-enemy', icon: '⚔️' },
  NEUTRAL: { label: 'Neutral', class: 'npc-type-neutral', icon: '🏪' },
  BOSS: { label: 'Boss', class: 'npc-type-boss', icon: '👹' },
  COMPANION: { label: 'Companion', class: 'npc-type-companion', icon: '🐺' }
}

export const NPC_STATUSES = {
  ACTIVE: { label: 'Active', class: 'npc-status-active' },
  DEFEATED: { label: 'Defeated', class: 'npc-status-defeated' },
  RETIRED: { label: 'Retired', class: 'npc-status-retired' }
}
