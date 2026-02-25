/**
 * Character Creator DOM Utilities
 * 
 * Functions for updating the DOM after state changes
 */

import { STAT_MIN, STAT_MAX } from './character-creator-constants.js'
import { calculateModifier, getInitials } from './character-creator-utils.js'

/**
 * Update the display for a single stat
 * @param {string} stat - The stat abbreviation
 * @param {number} value - The new value
 */
export function updateStatDisplay(stat, value) {
  const modifier = calculateModifier(value)
  const modifierStr = modifier >= 0 ? `+${modifier}` : `${modifier}`

  const valueEl = document.getElementById(`cc-stat-value-${stat}`)
  const modEl = document.getElementById(`cc-stat-mod-${stat}`)
  const card = document.querySelector(`.cc-stat-card[data-stat="${stat}"]`)
  
  if (valueEl) valueEl.textContent = value
  if (modEl) {
    modEl.textContent = modifierStr
    modEl.className = 'cc-stat-modifier'
    if (modifier > 0) modEl.classList.add('cc-stat-modifier-positive')
    else if (modifier < 0) modEl.classList.add('cc-stat-modifier-negative')
  }

  const decreaseBtn = card?.querySelector('[data-action="decrease"]')
  const increaseBtn = card?.querySelector('[data-action="increase"]')
  if (decreaseBtn) decreaseBtn.disabled = value <= STAT_MIN
  if (increaseBtn) increaseBtn.disabled = value >= STAT_MAX
}

/**
 * Update the points display
 * @param {number} pointsUsed - Points currently used
 * @param {number} maxPoints - Maximum points allowed
 */
export function updatePointsDisplay(pointsUsed, maxPoints) {
  const pointsRemaining = maxPoints - pointsUsed
  const pointsEl = document.getElementById('cc-points-current')
  
  if (pointsEl) {
    pointsEl.textContent = pointsRemaining
    pointsEl.className = 'cc-points-current'
    if (pointsRemaining < 0) {
      pointsEl.classList.add('cc-points-current-error')
    } else if (pointsRemaining === 0) {
      pointsEl.classList.add('cc-points-current-valid')
    } else {
      pointsEl.classList.add('cc-points-current-warning')
    }
  }
}

/**
 * Update the skills display
 * @param {Array<string>} selectedSkills - Currently selected skill names
 * @param {number} maxSkills - Maximum skills allowed
 */
export function updateSkillsDisplay(selectedSkills, maxSkills) {
  const skillItems = document.querySelectorAll('.cc-skill-item')
  skillItems.forEach(item => {
    const skillName = item.dataset.skill
    const isSelected = selectedSkills.includes(skillName)
    item.classList.toggle('selected', isSelected)
  })

  const counter = document.querySelector('.cc-skills-counter')
  if (counter) {
    const selectedCount = selectedSkills.length
    counter.textContent = `Selected: ${selectedCount} / ${maxSkills} skills`
    counter.className = 'cc-skills-counter'
    if (selectedCount === maxSkills) {
      counter.classList.add('cc-skills-counter-valid')
    } else if (selectedCount > maxSkills) {
      counter.classList.add('cc-skills-counter-error')
    }
  }
}

/**
 * Update the preview card
 * @param {Object} characterData - The character data
 */
export function updatePreview(characterData) {
  const name = characterData.name || 'Your Character'
  const race = characterData.race || '???'
  const cls = characterData.class || '???'
  const initials = getInitials(name)
  const conMod = calculateModifier(characterData.stats.CON)
  const hp = 10 + conMod

  const avatarEl = document.getElementById('cc-preview-avatar')
  const nameEl = document.getElementById('cc-preview-name')
  const detailsEl = document.getElementById('cc-preview-details')
  const hpEl = document.getElementById('cc-preview-hp')

  if (avatarEl) avatarEl.textContent = initials
  if (nameEl) nameEl.textContent = name
  if (detailsEl) detailsEl.textContent = `${race} ${cls} • Level 1`
  if (hpEl) hpEl.textContent = hp
}
