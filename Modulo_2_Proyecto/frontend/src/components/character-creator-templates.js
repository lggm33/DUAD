/**
 * Character Creator Templates
 * 
 * HTML template generation functions for the character creator UI
 */

import { escapeHtml } from '../utils/index.js'
import { 
  MODAL_ID, 
  STAT_NAMES, 
  STAT_MIN, 
  STAT_MAX,
  DEFAULT_RACES,
  DEFAULT_CLASSES,
  DEFAULT_SKILLS
} from './character-creator-constants.js'
import { calculateModifier, getInitials } from './character-creator-utils.js'

/**
 * Get the base modal HTML template
 * @returns {string} HTML string
 */
export function getModalTemplate() {
  return `
    <div id="${MODAL_ID}" class="character-creator-overlay" hidden>
      <div class="character-creator-modal">
        <div class="character-creator-header">
          <div class="character-creator-header-left">
            <div class="character-creator-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <h2 class="character-creator-title">Create Your Character</h2>
          </div>
          <button id="cc-close-btn" class="character-creator-close" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="character-creator-body" id="cc-form-container">
          <!-- Form content rendered dynamically -->
        </div>
        <div class="character-creator-footer">
          <div class="cc-footer-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <span>Character will be submitted for DM approval</span>
          </div>
          <div class="cc-footer-actions">
            <button id="cc-save-draft-btn" class="btn cc-btn-save-draft" type="button">
              Save Draft
            </button>
            <button id="cc-submit-btn" class="btn cc-btn-submit" type="button">
              Submit for Approval
            </button>
          </div>
        </div>
      </div>
    </div>
  `
}

/**
 * Render validation errors summary
 * @param {Array<string>} errors - Array of error messages
 * @returns {string} HTML string
 */
export function renderValidationSummary(errors) {
  if (errors.length === 0) return ''

  return `
    <div class="cc-validation-summary">
      <h4>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        Please fix the following errors:
      </h4>
      <ul>
        ${errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')}
      </ul>
    </div>
  `
}

/**
 * Render the basic info section (name, race, class)
 * @param {Object} characterData - The character data
 * @param {Object} rules - The game rules
 * @returns {string} HTML string
 */
export function renderBasicInfoSection(characterData, rules) {
  const races = rules.races || DEFAULT_RACES
  const classes = rules.classes || DEFAULT_CLASSES

  return `
    <div class="cc-form-section">
      <div class="cc-section-header">
        <svg class="cc-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
        <h3 class="cc-section-title">Basic Information</h3>
      </div>
      
      <div class="cc-form-grid">
        <div class="cc-form-group cc-form-full">
          <label class="cc-form-label cc-form-label-required" for="cc-name">Character Name</label>
          <input 
            type="text" 
            id="cc-name" 
            class="cc-form-input" 
            placeholder="Enter your character's name"
            value="${escapeHtml(characterData.name)}"
            maxlength="100"
            required
          />
        </div>
        
        <div class="cc-form-group">
          <label class="cc-form-label cc-form-label-required" for="cc-race">Race</label>
          <select id="cc-race" class="cc-form-select" required>
            <option value="">Select a race</option>
            ${races.map(race => `
              <option value="${escapeHtml(race)}" ${characterData.race === race ? 'selected' : ''}>
                ${escapeHtml(race)}
              </option>
            `).join('')}
          </select>
        </div>
        
        <div class="cc-form-group">
          <label class="cc-form-label cc-form-label-required" for="cc-class">Class</label>
          <select id="cc-class" class="cc-form-select" required>
            <option value="">Select a class</option>
            ${classes.map(cls => `
              <option value="${escapeHtml(cls)}" ${characterData.class === cls ? 'selected' : ''}>
                ${escapeHtml(cls)}
              </option>
            `).join('')}
          </select>
        </div>
        
        <div class="cc-form-group">
          <label class="cc-form-label" for="cc-background">Background</label>
          <input 
            type="text" 
            id="cc-background" 
            class="cc-form-input" 
            placeholder="e.g., Noble, Soldier..."
            value="${escapeHtml(characterData.background)}"
            maxlength="100"
          />
        </div>
      </div>
    </div>
  `
}

/**
 * Render the ability scores section with point-buy
 * @param {Object} stats - The ability scores
 * @param {number} pointsUsed - Points currently used
 * @param {number} maxPoints - Maximum points allowed
 * @returns {string} HTML string
 */
export function renderStatsSection(stats, pointsUsed, maxPoints) {
  const pointsRemaining = maxPoints - pointsUsed
  let pointsClass = 'cc-points-current-valid'
  if (pointsRemaining < 0) {
    pointsClass = 'cc-points-current-error'
  } else if (pointsRemaining > 0) {
    pointsClass = 'cc-points-current-warning'
  }

  return `
    <div class="cc-form-section">
      <div class="cc-section-header">
        <svg class="cc-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
        <h3 class="cc-section-title">Ability Scores</h3>
      </div>
      
      <div class="cc-points-counter">
        <span class="cc-points-label">Point Buy Remaining</span>
        <div class="cc-points-value">
          <span id="cc-points-current" class="cc-points-current ${pointsClass}">${pointsRemaining}</span>
          <span class="cc-points-total">/ ${maxPoints}</span>
        </div>
      </div>
      
      <div class="cc-stats-grid" id="cc-stats-grid">
        ${STAT_NAMES.map(stat => renderStatCard(stat, stats[stat])).join('')}
      </div>
    </div>
  `
}

/**
 * Render a single stat card
 * @param {string} stat - The stat abbreviation
 * @param {number} value - The stat value
 * @returns {string} HTML string
 */
export function renderStatCard(stat, value) {
  const modifier = calculateModifier(value)
  const modifierStr = modifier >= 0 ? `+${modifier}` : `${modifier}`
  const modifierClass = modifier > 0 ? 'cc-stat-modifier-positive' : 
                        modifier < 0 ? 'cc-stat-modifier-negative' : ''

  return `
    <div class="cc-stat-card" data-stat="${stat}">
      <div class="cc-stat-name">${stat}</div>
      <div class="cc-stat-controls">
        <button 
          type="button" 
          class="cc-stat-btn" 
          data-action="decrease" 
          data-stat="${stat}"
          ${value <= STAT_MIN ? 'disabled' : ''}
        >−</button>
        <span class="cc-stat-value" id="cc-stat-value-${stat}">${value}</span>
        <button 
          type="button" 
          class="cc-stat-btn" 
          data-action="increase" 
          data-stat="${stat}"
          ${value >= STAT_MAX ? 'disabled' : ''}
        >+</button>
      </div>
      <div class="cc-stat-modifier ${modifierClass}" id="cc-stat-mod-${stat}">${modifierStr}</div>
    </div>
  `
}

/**
 * Render the skills section
 * @param {Array<Object>} availableSkills - Available skills from rules
 * @param {Array<string>} selectedSkills - Currently selected skill names
 * @param {number} maxSkills - Maximum skills allowed
 * @returns {string} HTML string
 */
export function renderSkillsSection(availableSkills, selectedSkills, maxSkills) {
  const skills = availableSkills || DEFAULT_SKILLS
  const selectedCount = selectedSkills.length
  const counterClass = selectedCount === maxSkills ? 'cc-skills-counter-valid' :
                       selectedCount > maxSkills ? 'cc-skills-counter-error' : ''

  return `
    <div class="cc-form-section">
      <div class="cc-section-header">
        <svg class="cc-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <h3 class="cc-section-title">Skill Proficiencies</h3>
      </div>
      
      <p class="cc-skills-counter ${counterClass}">
        Selected: ${selectedCount} / ${maxSkills} skills
      </p>
      
      <div class="cc-skills-grid" id="cc-skills-grid">
        ${skills.map(skill => renderSkillItem(skill, selectedSkills)).join('')}
      </div>
    </div>
  `
}

/**
 * Render a single skill item
 * @param {Object} skill - The skill object
 * @param {Array<string>} selectedSkills - Currently selected skill names
 * @returns {string} HTML string
 */
export function renderSkillItem(skill, selectedSkills) {
  const isSelected = selectedSkills.includes(skill.name)
  return `
    <div 
      class="cc-skill-item ${isSelected ? 'selected' : ''}" 
      data-skill="${escapeHtml(skill.name)}"
    >
      <div class="cc-skill-checkbox">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </div>
      <span class="cc-skill-name">${escapeHtml(skill.name)}</span>
      <span class="cc-skill-stat">${skill.stat}</span>
    </div>
  `
}

/**
 * Render the description/backstory section
 * @param {string} description - The character description
 * @returns {string} HTML string
 */
export function renderDescriptionSection(description) {
  return `
    <div class="cc-form-section">
      <div class="cc-section-header">
        <svg class="cc-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <h3 class="cc-section-title">Character Background</h3>
      </div>
      
      <div class="cc-form-group">
        <label class="cc-form-label" for="cc-description">Backstory & Description</label>
        <textarea 
          id="cc-description" 
          class="cc-form-textarea" 
          placeholder="Tell us about your character's history, personality, goals..."
          rows="4"
          maxlength="2000"
        >${escapeHtml(description)}</textarea>
        <span class="cc-form-hint">Optional: Help the DM understand your character better</span>
      </div>
    </div>
  `
}

/**
 * Render the character preview card
 * @param {Object} characterData - The character data
 * @returns {string} HTML string
 */
export function renderPreviewCard(characterData) {
  const name = characterData.name || 'Your Character'
  const race = characterData.race || '???'
  const cls = characterData.class || '???'
  const initials = getInitials(name)
  const conMod = calculateModifier(characterData.stats.CON)
  const hp = 10 + conMod

  return `
    <div class="cc-form-section">
      <div class="cc-section-header">
        <svg class="cc-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
        <h3 class="cc-section-title">Preview</h3>
      </div>
      
      <div class="cc-preview-card" id="cc-preview-card">
        <div class="cc-preview-avatar" id="cc-preview-avatar">${initials}</div>
        <div class="cc-preview-info">
          <h4 class="cc-preview-name" id="cc-preview-name">${escapeHtml(name)}</h4>
          <p class="cc-preview-details" id="cc-preview-details">
            ${escapeHtml(race)} ${escapeHtml(cls)} • Level 1
          </p>
        </div>
        <div class="cc-preview-stats">
          <div class="cc-preview-stat">
            <div class="cc-preview-stat-value" id="cc-preview-hp">${hp}</div>
            <div class="cc-preview-stat-label">HP</div>
          </div>
          <div class="cc-preview-stat">
            <div class="cc-preview-stat-value" id="cc-preview-ac">10</div>
            <div class="cc-preview-stat-label">AC</div>
          </div>
        </div>
      </div>
    </div>
  `
}
