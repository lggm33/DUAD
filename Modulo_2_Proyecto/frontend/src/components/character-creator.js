/**
 * CharacterCreator Component
 * 
 * A dynamic form component that generates character creation fields
 * based on the game's ruleset. Supports point-buy stats, skill selection,
 * and validation according to the game rules.
 */

import { fetchWithAuth, escapeHtml } from '../utils/index.js'

const MODAL_ID = 'character-creator-modal'

const STAT_NAMES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
const STAT_FULL_NAMES = {
  STR: 'Strength',
  DEX: 'Dexterity',
  CON: 'Constitution',
  INT: 'Intelligence',
  WIS: 'Wisdom',
  CHA: 'Charisma'
}

const DEFAULT_SKILLS = [
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

const DEFAULT_RACES = [
  'Human', 'Elf', 'Dwarf', 'Halfling', 'Dragonborn',
  'Gnome', 'Half-Elf', 'Half-Orc', 'Tiefling'
]

const DEFAULT_CLASSES = [
  'Barbarian', 'Bard', 'Cleric', 'Druid', 'Fighter',
  'Monk', 'Paladin', 'Ranger', 'Rogue', 'Sorcerer',
  'Warlock', 'Wizard'
]

const POINT_BUY_COSTS = {
  8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9
}

const DEFAULT_POINT_BUY_TOTAL = 27
const STAT_MIN = 8
const STAT_MAX = 15
const DEFAULT_SKILL_COUNT = 2

export class CharacterCreator {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.gameId - The ID of the game
   * @param {Object} options.rules - The game's ruleset configuration
   * @param {Function} options.onSubmit - Callback when character is submitted
   * @param {Function} options.onCancel - Callback when creation is cancelled
   * @param {Function} options.onSaveDraft - Callback when saving as draft
   */
  constructor(options) {
    this.gameId = options.gameId
    this.rules = options.rules || {}
    this.onSubmit = options.onSubmit
    this.onCancel = options.onCancel
    this.onSaveDraft = options.onSaveDraft

    this.characterData = {
      name: '',
      race: '',
      class: '',
      level: 1,
      background: '',
      stats: {
        STR: 10, DEX: 10, CON: 10, INT: 10, WIS: 10, CHA: 10
      },
      skills: [],
      description: ''
    }

    this.pointsUsed = 0
    this.maxPoints = this.rules.point_buy_total || DEFAULT_POINT_BUY_TOTAL
    this.maxSkills = this.rules.skill_count || DEFAULT_SKILL_COUNT
    this.errors = []
    this.isSubmitting = false
  }

  /**
   * Initialize and show the character creator modal
   */
  init() {
    this.ensureModalExists()
    this.renderForm()
    this.setupEventListeners()
    this.updatePointsDisplay()
    this.show()
  }

  /**
   * Ensure the modal container exists in the DOM
   */
  ensureModalExists() {
    if (!document.getElementById(MODAL_ID)) {
      document.body.insertAdjacentHTML('beforeend', this.getModalTemplate())
    }
  }

  /**
   * Get the base modal HTML template
   */
  getModalTemplate() {
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
   * Render the complete form content
   */
  renderForm() {
    const container = document.getElementById('cc-form-container')
    if (!container) return

    container.innerHTML = `
      ${this.renderValidationSummary()}
      ${this.renderBasicInfoSection()}
      ${this.renderStatsSection()}
      ${this.renderSkillsSection()}
      ${this.renderDescriptionSection()}
      ${this.renderPreviewCard()}
    `
  }

  /**
   * Render validation errors summary
   */
  renderValidationSummary() {
    if (this.errors.length === 0) return ''

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
          ${this.errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')}
        </ul>
      </div>
    `
  }

  /**
   * Render the basic info section (name, race, class)
   */
  renderBasicInfoSection() {
    const races = this.rules.races || DEFAULT_RACES
    const classes = this.rules.classes || DEFAULT_CLASSES

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
              value="${escapeHtml(this.characterData.name)}"
              maxlength="100"
              required
            />
          </div>
          
          <div class="cc-form-group">
            <label class="cc-form-label cc-form-label-required" for="cc-race">Race</label>
            <select id="cc-race" class="cc-form-select" required>
              <option value="">Select a race</option>
              ${races.map(race => `
                <option value="${escapeHtml(race)}" ${this.characterData.race === race ? 'selected' : ''}>
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
                <option value="${escapeHtml(cls)}" ${this.characterData.class === cls ? 'selected' : ''}>
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
              value="${escapeHtml(this.characterData.background)}"
              maxlength="100"
            />
          </div>
        </div>
      </div>
    `
  }

  /**
   * Render the ability scores section with point-buy
   */
  renderStatsSection() {
    const pointsRemaining = this.maxPoints - this.pointsUsed
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
            <span class="cc-points-total">/ ${this.maxPoints}</span>
          </div>
        </div>
        
        <div class="cc-stats-grid" id="cc-stats-grid">
          ${STAT_NAMES.map(stat => this.renderStatCard(stat)).join('')}
        </div>
      </div>
    `
  }

  /**
   * Render a single stat card
   */
  renderStatCard(stat) {
    const value = this.characterData.stats[stat]
    const modifier = this.calculateModifier(value)
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
   */
  renderSkillsSection() {
    const skills = this.rules.skills || DEFAULT_SKILLS
    const selectedCount = this.characterData.skills.length
    const counterClass = selectedCount === this.maxSkills ? 'cc-skills-counter-valid' :
                         selectedCount > this.maxSkills ? 'cc-skills-counter-error' : ''

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
          Selected: ${selectedCount} / ${this.maxSkills} skills
        </p>
        
        <div class="cc-skills-grid" id="cc-skills-grid">
          ${skills.map(skill => this.renderSkillItem(skill)).join('')}
        </div>
      </div>
    `
  }

  /**
   * Render a single skill item
   */
  renderSkillItem(skill) {
    const isSelected = this.characterData.skills.includes(skill.name)
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
   */
  renderDescriptionSection() {
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
          >${escapeHtml(this.characterData.description)}</textarea>
          <span class="cc-form-hint">Optional: Help the DM understand your character better</span>
        </div>
      </div>
    `
  }

  /**
   * Render the character preview card
   */
  renderPreviewCard() {
    const name = this.characterData.name || 'Your Character'
    const race = this.characterData.race || '???'
    const cls = this.characterData.class || '???'
    const initials = this.getInitials(name)
    const conMod = this.calculateModifier(this.characterData.stats.CON)
    const hp = 10 + conMod  // Simplified HP calculation

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

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    const modal = document.getElementById(MODAL_ID)
    if (!modal) return

    // Close button
    const closeBtn = document.getElementById('cc-close-btn')
    closeBtn?.addEventListener('click', () => this.handleCancel())

    // Click outside to close
    modal.addEventListener('click', (e) => {
      if (e.target === modal) this.handleCancel()
    })

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) {
        this.handleCancel()
      }
    })

    // Form inputs
    this.setupFormInputListeners()

    // Stat buttons
    this.setupStatButtonListeners()

    // Skill selection
    this.setupSkillListeners()

    // Footer buttons
    document.getElementById('cc-save-draft-btn')?.addEventListener('click', () => this.handleSaveDraft())
    document.getElementById('cc-submit-btn')?.addEventListener('click', () => this.handleSubmit())
  }

  /**
   * Setup listeners for form input changes
   */
  setupFormInputListeners() {
    const nameInput = document.getElementById('cc-name')
    const raceSelect = document.getElementById('cc-race')
    const classSelect = document.getElementById('cc-class')
    const backgroundInput = document.getElementById('cc-background')
    const descriptionTextarea = document.getElementById('cc-description')

    nameInput?.addEventListener('input', (e) => {
      this.characterData.name = e.target.value
      this.updatePreview()
    })

    raceSelect?.addEventListener('change', (e) => {
      this.characterData.race = e.target.value
      this.updatePreview()
    })

    classSelect?.addEventListener('change', (e) => {
      this.characterData.class = e.target.value
      this.updatePreview()
    })

    backgroundInput?.addEventListener('input', (e) => {
      this.characterData.background = e.target.value
    })

    descriptionTextarea?.addEventListener('input', (e) => {
      this.characterData.description = e.target.value
    })
  }

  /**
   * Setup listeners for stat increase/decrease buttons
   */
  setupStatButtonListeners() {
    const statButtons = document.querySelectorAll('.cc-stat-btn')
    statButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const stat = btn.dataset.stat
        const action = btn.dataset.action
        this.handleStatChange(stat, action)
      })
    })
  }

  /**
   * Setup listeners for skill selection
   */
  setupSkillListeners() {
    const skillItems = document.querySelectorAll('.cc-skill-item')
    skillItems.forEach(item => {
      item.addEventListener('click', () => {
        const skillName = item.dataset.skill
        this.handleSkillToggle(skillName)
      })
    })
  }

  /**
   * Handle stat value change
   */
  handleStatChange(stat, action) {
    const currentValue = this.characterData.stats[stat]
    let newValue = currentValue

    if (action === 'increase' && currentValue < STAT_MAX) {
      newValue = currentValue + 1
    } else if (action === 'decrease' && currentValue > STAT_MIN) {
      newValue = currentValue - 1
    }

    if (newValue !== currentValue) {
      this.characterData.stats[stat] = newValue
      this.recalculatePoints()
      this.updateStatDisplay(stat)
      this.updatePointsDisplay()
      this.updatePreview()
    }
  }

  /**
   * Handle skill toggle
   */
  handleSkillToggle(skillName) {
    const index = this.characterData.skills.indexOf(skillName)
    if (index > -1) {
      this.characterData.skills.splice(index, 1)
    } else if (this.characterData.skills.length < this.maxSkills) {
      this.characterData.skills.push(skillName)
    }
    this.updateSkillsDisplay()
  }

  /**
   * Calculate ability modifier from score
   */
  calculateModifier(score) {
    return Math.floor((score - 10) / 2)
  }

  /**
   * Recalculate total points used
   */
  recalculatePoints() {
    this.pointsUsed = 0
    for (const stat of STAT_NAMES) {
      const value = this.characterData.stats[stat]
      this.pointsUsed += POINT_BUY_COSTS[value] || 0
    }
  }

  /**
   * Update the display for a single stat
   */
  updateStatDisplay(stat) {
    const value = this.characterData.stats[stat]
    const modifier = this.calculateModifier(value)
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

    // Update button states
    const decreaseBtn = card?.querySelector('[data-action="decrease"]')
    const increaseBtn = card?.querySelector('[data-action="increase"]')
    if (decreaseBtn) decreaseBtn.disabled = value <= STAT_MIN
    if (increaseBtn) increaseBtn.disabled = value >= STAT_MAX
  }

  /**
   * Update the points display
   */
  updatePointsDisplay() {
    const pointsRemaining = this.maxPoints - this.pointsUsed
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
   */
  updateSkillsDisplay() {
    const skillItems = document.querySelectorAll('.cc-skill-item')
    skillItems.forEach(item => {
      const skillName = item.dataset.skill
      const isSelected = this.characterData.skills.includes(skillName)
      item.classList.toggle('selected', isSelected)
    })

    // Update counter
    const counter = document.querySelector('.cc-skills-counter')
    if (counter) {
      const selectedCount = this.characterData.skills.length
      counter.textContent = `Selected: ${selectedCount} / ${this.maxSkills} skills`
      counter.className = 'cc-skills-counter'
      if (selectedCount === this.maxSkills) {
        counter.classList.add('cc-skills-counter-valid')
      } else if (selectedCount > this.maxSkills) {
        counter.classList.add('cc-skills-counter-error')
      }
    }
  }

  /**
   * Update the preview card
   */
  updatePreview() {
    const name = this.characterData.name || 'Your Character'
    const race = this.characterData.race || '???'
    const cls = this.characterData.class || '???'
    const initials = this.getInitials(name)
    const conMod = this.calculateModifier(this.characterData.stats.CON)
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

  /**
   * Get initials from name
   */
  getInitials(name) {
    if (!name) return '?'
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('')
  }

  /**
   * Validate the character data
   */
  validate() {
    this.errors = []

    if (!this.characterData.name.trim()) {
      this.errors.push('Character name is required')
    }

    if (!this.characterData.race) {
      this.errors.push('Please select a race')
    }

    if (!this.characterData.class) {
      this.errors.push('Please select a class')
    }

    const pointsRemaining = this.maxPoints - this.pointsUsed
    if (pointsRemaining !== 0) {
      this.errors.push(`You must use exactly ${this.maxPoints} points for ability scores`)
    }

    if (this.characterData.skills.length !== this.maxSkills) {
      this.errors.push(`You must select exactly ${this.maxSkills} skill proficiencies`)
    }

    return this.errors.length === 0
  }

  /**
   * Build the character data payload for API
   */
  buildPayload(status = 'PENDING_APPROVAL') {
    return {
      name: this.characterData.name.trim(),
      status: status,
      data: {
        race: this.characterData.race,
        class: this.characterData.class,
        level: 1,
        background: this.characterData.background,
        abilities: this.characterData.stats,
        skills: this.characterData.skills,
        description: this.characterData.description,
        hp: 10 + this.calculateModifier(this.characterData.stats.CON),
        ac: 10
      }
    }
  }

  /**
   * Handle save as draft
   */
  async handleSaveDraft() {
    // For draft, we allow partial data
    if (!this.characterData.name.trim()) {
      this.errors = ['Please enter a character name to save as draft']
      this.renderForm()
      this.setupFormInputListeners()
      this.setupStatButtonListeners()
      this.setupSkillListeners()
      return
    }

    try {
      const payload = this.buildPayload('DRAFT')
      const response = await fetchWithAuth(`/api/v1/game/${this.gameId}/character`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to save draft')
      }

      const character = await response.json()
      this.hide()
      if (this.onSaveDraft) {
        this.onSaveDraft(character)
      }
    } catch (error) {
      this.errors = [error.message]
      this.renderForm()
      this.setupFormInputListeners()
      this.setupStatButtonListeners()
      this.setupSkillListeners()
    }
  }

  /**
   * Handle form submission
   */
  async handleSubmit() {
    if (this.isSubmitting) return

    if (!this.validate()) {
      this.renderForm()
      this.setupFormInputListeners()
      this.setupStatButtonListeners()
      this.setupSkillListeners()
      return
    }

    this.isSubmitting = true
    const submitBtn = document.getElementById('cc-submit-btn')
    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.textContent = 'Submitting...'
    }

    try {
      const payload = this.buildPayload('PENDING_APPROVAL')
      const response = await fetchWithAuth(`/api/v1/game/${this.gameId}/character`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to create character')
      }

      const character = await response.json()
      this.hide()
      if (this.onSubmit) {
        this.onSubmit(character)
      }
    } catch (error) {
      this.errors = [error.message]
      this.renderForm()
      this.setupFormInputListeners()
      this.setupStatButtonListeners()
      this.setupSkillListeners()
    } finally {
      this.isSubmitting = false
      if (submitBtn) {
        submitBtn.disabled = false
        submitBtn.textContent = 'Submit for Approval'
      }
    }
  }

  /**
   * Handle cancel action
   */
  handleCancel() {
    this.hide()
    if (this.onCancel) {
      this.onCancel()
    }
  }

  /**
   * Show the modal
   */
  show() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = false
      document.body.style.overflow = 'hidden'
    }
  }

  /**
   * Hide the modal
   */
  hide() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = true
      document.body.style.overflow = ''
    }
  }

  /**
   * Destroy the modal and cleanup
   */
  destroy() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.remove()
    }
    document.body.style.overflow = ''
  }
}

