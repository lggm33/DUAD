/**
 * Character Creator Utilities
 * 
 * Pure functions for calculations and data transformation
 */

import { STAT_NAMES, POINT_BUY_COSTS } from './character-creator-constants.js'

/**
 * Calculate ability modifier from score
 * @param {number} score - The ability score
 * @returns {number} The modifier
 */
export function calculateModifier(score) {
  return Math.floor((score - 10) / 2)
}

/**
 * Recalculate total points used in point buy system
 * @param {Object} stats - The stats object with all ability scores
 * @returns {number} Total points used
 */
export function recalculatePoints(stats) {
  let pointsUsed = 0
  for (const stat of STAT_NAMES) {
    const value = stats[stat]
    pointsUsed += POINT_BUY_COSTS[value] || 0
  }
  return pointsUsed
}

/**
 * Get initials from name
 * @param {string} name - The character name
 * @returns {string} Initials (max 2 characters)
 */
export function getInitials(name) {
  if (!name) return '?'
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('')
}

/**
 * Validate the character data
 * @param {Object} characterData - The character data to validate
 * @param {number} pointsUsed - Points used in point buy
 * @param {number} maxPoints - Maximum points allowed
 * @param {number} maxSkills - Maximum skills allowed
 * @returns {Array<string>} Array of error messages (empty if valid)
 */
export function validateCharacter(characterData, pointsUsed, maxPoints, maxSkills) {
  const errors = []

  if (!characterData.name.trim()) {
    errors.push('Character name is required')
  }

  if (!characterData.race) {
    errors.push('Please select a race')
  }

  if (!characterData.class) {
    errors.push('Please select a class')
  }

  const pointsRemaining = maxPoints - pointsUsed
  if (pointsRemaining !== 0) {
    errors.push(`You must use exactly ${maxPoints} points for ability scores`)
  }

  if (characterData.skills.length !== maxSkills) {
    errors.push(`You must select exactly ${maxSkills} skill proficiencies`)
  }

  return errors
}

/**
 * Build the character data payload for API
 * @param {Object} characterData - The character data
 * @param {boolean} submitForApproval - Whether to submit for approval
 * @returns {Object} The payload for API
 */
export function buildPayload(characterData, submitForApproval = false) {
  return {
    name: characterData.name.trim(),
    submit_for_approval: submitForApproval,
    data: {
      race: characterData.race,
      class: characterData.class,
      level: 1,
      background: characterData.background,
      abilities: characterData.stats,
      skills: characterData.skills,
      description: characterData.description,
      hp: 10 + calculateModifier(characterData.stats.CON),
      ac: 10
    }
  }
}
