/**
 * CharacterSheet Component
 * 
 * A read-only/editable view of a character with stats, skills,
 * combat information, features, and equipment. Supports inline
 * editing for HP and notes when the user is the owner and the
 * character status is APPROVED.
 */

import { fetchWithAuth, escapeHtml, getInitials } from '../utils/index.js'

const MODAL_ID = 'character-sheet-modal'

const STAT_NAMES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
const STAT_FULL_NAMES = {
  STR: 'Strength',
  DEX: 'Dexterity',
  CON: 'Constitution',
  INT: 'Intelligence',
  WIS: 'Wisdom',
  CHA: 'Charisma'
}

const STATUS_LABELS = {
  DRAFT: { label: 'Draft', class: 'cs-status-draft' },
  PENDING_APPROVAL: { label: 'Pending Approval', class: 'cs-status-pending' },
  APPROVED: { label: 'Approved', class: 'cs-status-approved' },
  REJECTED: { label: 'Rejected', class: 'cs-status-rejected' }
}

export class CharacterSheet {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.gameId - The ID of the game
   * @param {number} options.characterId - The ID of the character to display
   * @param {boolean} options.isEditable - Whether the sheet is editable
   * @param {Function} options.onUpdate - Callback when character is updated
   * @param {Function} options.onClose - Callback when sheet is closed
   */
  constructor(options) {
    this.gameId = options.gameId
    this.characterId = options.characterId
    this.isEditable = options.isEditable || false
    this.onUpdate = options.onUpdate
    this.onClose = options.onClose

    this.character = null
    this.isLoading = true
    this.error = null
    this.isSaving = false
    this.editMode = false
    this.pendingChanges = {}
  }

  /**
   * Initialize and show the character sheet modal
   */
  async init() {
    this.ensureModalExists()
    this.show()
    this.renderLoading()
    await this.loadCharacter()
  }

  /**
   * Load character data from API
   */
  async loadCharacter() {
    try {
      this.isLoading = true
      this.error = null
      this.renderLoading()

      const response = await fetchWithAuth(
        `/api/v1/game/${this.gameId}/character/${this.characterId}`
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to load character')
      }

      this.character = await response.json()
      this.isLoading = false
      this.renderSheet()
      this.setupEventListeners()
    } catch (error) {
      this.error = error.message
      this.isLoading = false
      this.renderError()
    }
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
      <div id="${MODAL_ID}" class="character-sheet-overlay" hidden>
        <div class="character-sheet-modal">
          <div class="character-sheet-header">
            <div class="character-sheet-header-left">
              <div class="character-sheet-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </div>
              <h2 class="character-sheet-title">Character Sheet</h2>
            </div>
            <div class="character-sheet-header-actions">
              <button id="cs-edit-btn" class="cs-action-btn" type="button" hidden>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
                <span>Edit</span>
              </button>
              <button id="cs-close-btn" class="character-sheet-close" type="button">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
          <div class="character-sheet-body" id="cs-content">
            <!-- Content rendered dynamically -->
          </div>
          <div class="character-sheet-footer" id="cs-footer">
            <!-- Footer rendered dynamically -->
          </div>
        </div>
      </div>
    `
  }

  /**
   * Render loading state
   */
  renderLoading() {
    const container = document.getElementById('cs-content')
    if (!container) return

    container.innerHTML = `
      <div class="cs-loading">
        <div class="cs-loading-spinner"></div>
        <p>Loading character...</p>
      </div>
    `

    this.hideFooter()
  }

  /**
   * Render error state
   */
  renderError() {
    const container = document.getElementById('cs-content')
    if (!container) return

    container.innerHTML = `
      <div class="cs-error">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <h3>Failed to Load Character</h3>
        <p>${escapeHtml(this.error)}</p>
        <button class="btn cs-btn-retry" id="cs-retry-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
          Try Again
        </button>
      </div>
    `

    document.getElementById('cs-retry-btn')?.addEventListener('click', () => this.loadCharacter())
    this.hideFooter()
  }

  /**
   * Render the complete character sheet
   */
  renderSheet() {
    const container = document.getElementById('cs-content')
    if (!container || !this.character) return

    const data = this.character.data || {}
    
    container.innerHTML = `
      ${this.renderHeroSection()}
      ${this.renderCombatStats()}
      ${this.renderAbilityScores()}
      ${this.renderSkillsSection()}
      ${this.renderFeaturesSection()}
      ${this.renderEquipmentSection()}
      ${this.renderBackstorySection()}
      ${this.renderDMFeedback()}
    `

    this.renderFooter()
    this.updateEditButton()
  }

  /**
   * Render the hero section (avatar, name, class, race)
   */
  renderHeroSection() {
    const data = this.character.data || {}
    const name = this.character.name || 'Unknown Character'
    const initials = getInitials(name)
    const race = data.race || 'Unknown Race'
    const charClass = data.class || 'Unknown Class'
    const level = data.level || 1
    const background = data.background || ''
    const status = STATUS_LABELS[this.character.status] || STATUS_LABELS.DRAFT

    return `
      <div class="cs-hero-section">
        <div class="cs-avatar">${initials}</div>
        <div class="cs-hero-info">
          <div class="cs-name-row">
            <h2 class="cs-character-name">${escapeHtml(name)}</h2>
            <span class="cs-status-badge ${status.class}">${status.label}</span>
          </div>
          <p class="cs-character-subtitle">
            ${escapeHtml(race)} ${escapeHtml(charClass)} • Level ${level}
          </p>
          ${background ? `<p class="cs-character-background">${escapeHtml(background)}</p>` : ''}
        </div>
      </div>
    `
  }

  /**
   * Render combat stats (HP, AC, Speed, Initiative)
   */
  renderCombatStats() {
    const data = this.character.data || {}
    const abilities = data.abilities || {}
    
    const currentHP = this.editMode && this.pendingChanges.current_hp !== undefined 
      ? this.pendingChanges.current_hp 
      : (data.current_hp !== undefined ? data.current_hp : data.hp)
    const maxHP = data.hp || 10
    const tempHP = data.temp_hp || 0
    const ac = data.ac || 10
    const speed = data.speed || 30
    const initiativeBonus = this.calculateModifier(abilities.DEX || 10)
    const initiativeStr = initiativeBonus >= 0 ? `+${initiativeBonus}` : `${initiativeBonus}`
    
    const hpPercentage = Math.min(100, Math.max(0, (currentHP / maxHP) * 100))
    const hpBarClass = hpPercentage > 50 ? 'cs-hp-bar-healthy' : 
                       hpPercentage > 25 ? 'cs-hp-bar-wounded' : 'cs-hp-bar-critical'

    return `
      <div class="cs-combat-section">
        <div class="cs-combat-grid">
          <div class="cs-combat-stat cs-combat-stat-hp">
            <div class="cs-combat-stat-label">Hit Points</div>
            <div class="cs-hp-display">
              ${this.editMode ? `
                <input 
                  type="number" 
                  id="cs-current-hp" 
                  class="cs-hp-input" 
                  value="${currentHP}" 
                  min="0" 
                  max="${maxHP + 100}"
                />
              ` : `
                <span class="cs-hp-current">${currentHP}</span>
              `}
              <span class="cs-hp-separator">/</span>
              <span class="cs-hp-max">${maxHP}</span>
              ${tempHP > 0 ? `<span class="cs-hp-temp">+${tempHP}</span>` : ''}
            </div>
            <div class="cs-hp-bar-container">
              <div class="cs-hp-bar ${hpBarClass}" style="width: ${hpPercentage}%"></div>
            </div>
          </div>
          
          <div class="cs-combat-stat">
            <div class="cs-combat-stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
            </div>
            <div class="cs-combat-stat-value">${ac}</div>
            <div class="cs-combat-stat-label">Armor Class</div>
          </div>
          
          <div class="cs-combat-stat">
            <div class="cs-combat-stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
              </svg>
            </div>
            <div class="cs-combat-stat-value">${speed}ft</div>
            <div class="cs-combat-stat-label">Speed</div>
          </div>
          
          <div class="cs-combat-stat">
            <div class="cs-combat-stat-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
            </div>
            <div class="cs-combat-stat-value">${initiativeStr}</div>
            <div class="cs-combat-stat-label">Initiative</div>
          </div>
        </div>
      </div>
    `
  }

  /**
   * Render ability scores section
   */
  renderAbilityScores() {
    const data = this.character.data || {}
    const abilities = data.abilities || {}

    return `
      <div class="cs-section">
        <div class="cs-section-header">
          <svg class="cs-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
          </svg>
          <h3 class="cs-section-title">Ability Scores</h3>
        </div>
        
        <div class="cs-abilities-grid">
          ${STAT_NAMES.map(stat => this.renderAbilityCard(stat, abilities[stat] || 10)).join('')}
        </div>
      </div>
    `
  }

  /**
   * Render a single ability card
   */
  renderAbilityCard(stat, value) {
    const modifier = this.calculateModifier(value)
    const modifierStr = modifier >= 0 ? `+${modifier}` : `${modifier}`
    const modifierClass = modifier > 0 ? 'cs-ability-modifier-positive' : 
                          modifier < 0 ? 'cs-ability-modifier-negative' : ''

    return `
      <div class="cs-ability-card">
        <div class="cs-ability-name">${stat}</div>
        <div class="cs-ability-score">${value}</div>
        <div class="cs-ability-modifier ${modifierClass}">${modifierStr}</div>
      </div>
    `
  }

  /**
   * Render skills section
   */
  renderSkillsSection() {
    const data = this.character.data || {}
    const skills = data.skills || []
    const abilities = data.abilities || {}

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

    return `
      <div class="cs-section">
        <div class="cs-section-header">
          <svg class="cs-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          <h3 class="cs-section-title">Skills</h3>
        </div>
        
        <div class="cs-skills-grid">
          ${DEFAULT_SKILLS.map(skill => {
            const isProficient = skills.includes(skill.name)
            const abilityMod = this.calculateModifier(abilities[skill.stat] || 10)
            const profBonus = isProficient ? 2 : 0 // Simplified proficiency bonus
            const totalBonus = abilityMod + profBonus
            const bonusStr = totalBonus >= 0 ? `+${totalBonus}` : `${totalBonus}`
            
            return `
              <div class="cs-skill-row ${isProficient ? 'cs-skill-proficient' : ''}">
                <span class="cs-skill-proficiency">
                  ${isProficient ? '●' : '○'}
                </span>
                <span class="cs-skill-name">${escapeHtml(skill.name)}</span>
                <span class="cs-skill-stat">${skill.stat}</span>
                <span class="cs-skill-bonus">${bonusStr}</span>
              </div>
            `
          }).join('')}
        </div>
      </div>
    `
  }

  /**
   * Render features section
   */
  renderFeaturesSection() {
    const data = this.character.data || {}
    const features = data.features || []
    
    if (features.length === 0) return ''

    return `
      <div class="cs-section">
        <div class="cs-section-header">
          <svg class="cs-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
          </svg>
          <h3 class="cs-section-title">Features & Traits</h3>
        </div>
        
        <div class="cs-features-list">
          ${features.map(feature => `
            <div class="cs-feature-item">
              <h4 class="cs-feature-name">${escapeHtml(feature.name || feature)}</h4>
              ${feature.description ? `<p class="cs-feature-desc">${escapeHtml(feature.description)}</p>` : ''}
            </div>
          `).join('')}
        </div>
      </div>
    `
  }

  /**
   * Render equipment section
   */
  renderEquipmentSection() {
    const data = this.character.data || {}
    const equipment = data.equipment || []
    
    if (equipment.length === 0) return ''

    return `
      <div class="cs-section">
        <div class="cs-section-header">
          <svg class="cs-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path>
            <line x1="16" y1="8" x2="2" y2="22"></line>
            <line x1="17.5" y1="15" x2="9" y2="15"></line>
          </svg>
          <h3 class="cs-section-title">Equipment</h3>
        </div>
        
        <div class="cs-equipment-grid">
          ${equipment.map(item => `
            <div class="cs-equipment-item">
              <span class="cs-equipment-name">${escapeHtml(typeof item === 'string' ? item : item.name)}</span>
              ${item.quantity && item.quantity > 1 ? `<span class="cs-equipment-qty">×${item.quantity}</span>` : ''}
            </div>
          `).join('')}
        </div>
      </div>
    `
  }

  /**
   * Render backstory section
   */
  renderBackstorySection() {
    const data = this.character.data || {}
    const description = data.description || ''
    
    if (!description && !this.editMode) return ''

    return `
      <div class="cs-section">
        <div class="cs-section-header">
          <svg class="cs-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          <h3 class="cs-section-title">Backstory</h3>
        </div>
        
        ${this.editMode ? `
          <textarea 
            id="cs-description" 
            class="cs-description-textarea"
            placeholder="Character backstory and notes..."
          >${escapeHtml(this.pendingChanges.description !== undefined ? this.pendingChanges.description : description)}</textarea>
        ` : `
          <p class="cs-description-text">${escapeHtml(description) || 'No backstory provided.'}</p>
        `}
      </div>
    `
  }

  /**
   * Render DM feedback section (if rejected)
   */
  renderDMFeedback() {
    const feedback = this.character.dm_feedback
    if (!feedback || this.character.status !== 'REJECTED') return ''

    return `
      <div class="cs-section cs-dm-feedback">
        <div class="cs-section-header">
          <svg class="cs-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <h3 class="cs-section-title">DM Feedback</h3>
        </div>
        
        <div class="cs-feedback-content">
          <p>${escapeHtml(feedback)}</p>
        </div>
      </div>
    `
  }

  /**
   * Render the footer with actions
   */
  renderFooter() {
    const footer = document.getElementById('cs-footer')
    if (!footer) return

    footer.hidden = false

    if (this.editMode) {
      footer.innerHTML = `
        <div class="cs-footer-info">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>Editing character information</span>
        </div>
        <div class="cs-footer-actions">
          <button id="cs-cancel-edit-btn" class="btn cs-btn-cancel" type="button">
            Cancel
          </button>
          <button id="cs-save-btn" class="btn cs-btn-save" type="button">
            Save Changes
          </button>
        </div>
      `
      
      document.getElementById('cs-cancel-edit-btn')?.addEventListener('click', () => this.cancelEdit())
      document.getElementById('cs-save-btn')?.addEventListener('click', () => this.saveChanges())
    } else {
      footer.innerHTML = `
        <div class="cs-footer-info">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>Last updated: ${this.formatDate(this.character.updated_at)}</span>
        </div>
        <div class="cs-footer-actions">
          <button id="cs-close-footer-btn" class="btn cs-btn-close" type="button">
            Close
          </button>
        </div>
      `
      
      document.getElementById('cs-close-footer-btn')?.addEventListener('click', () => this.handleClose())
    }
  }

  /**
   * Hide the footer
   */
  hideFooter() {
    const footer = document.getElementById('cs-footer')
    if (footer) footer.hidden = true
  }

  /**
   * Update edit button visibility
   */
  updateEditButton() {
    const editBtn = document.getElementById('cs-edit-btn')
    if (!editBtn) return

    const canEdit = this.isEditable && this.character.status === 'APPROVED'
    editBtn.hidden = !canEdit || this.editMode
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    const modal = document.getElementById(MODAL_ID)
    if (!modal) return

    // Close button
    const closeBtn = document.getElementById('cs-close-btn')
    closeBtn?.addEventListener('click', () => this.handleClose())

    // Click outside to close
    modal.addEventListener('click', (e) => {
      if (e.target === modal) this.handleClose()
    })

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) {
        this.handleClose()
      }
    })

    // Edit button
    document.getElementById('cs-edit-btn')?.addEventListener('click', () => this.enableEdit())
  }

  /**
   * Enable edit mode
   */
  enableEdit() {
    this.editMode = true
    this.pendingChanges = {}
    this.renderSheet()
    this.setupEditListeners()
  }

  /**
   * Setup listeners for edit mode inputs
   */
  setupEditListeners() {
    const hpInput = document.getElementById('cs-current-hp')
    const descInput = document.getElementById('cs-description')

    hpInput?.addEventListener('input', (e) => {
      this.pendingChanges.current_hp = parseInt(e.target.value) || 0
    })

    descInput?.addEventListener('input', (e) => {
      this.pendingChanges.description = e.target.value
    })
  }

  /**
   * Cancel edit mode
   */
  cancelEdit() {
    this.editMode = false
    this.pendingChanges = {}
    this.renderSheet()
    this.setupEventListeners()
  }

  /**
   * Save changes to the character
   */
  async saveChanges() {
    if (this.isSaving) return

    this.isSaving = true
    const saveBtn = document.getElementById('cs-save-btn')
    if (saveBtn) {
      saveBtn.disabled = true
      saveBtn.textContent = 'Saving...'
    }

    try {
      const data = { ...this.character.data }
      
      if (this.pendingChanges.current_hp !== undefined) {
        data.current_hp = this.pendingChanges.current_hp
      }
      
      if (this.pendingChanges.description !== undefined) {
        data.description = this.pendingChanges.description
      }

      const response = await fetchWithAuth(
        `/api/v1/game/${this.gameId}/character/${this.characterId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data })
        }
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to save changes')
      }

      this.character = await response.json()
      this.editMode = false
      this.pendingChanges = {}
      this.renderSheet()
      this.setupEventListeners()

      if (this.onUpdate) {
        this.onUpdate(this.character)
      }
    } catch (error) {
      console.error('Failed to save character:', error)
      alert(`Error saving character: ${error.message}`)
    } finally {
      this.isSaving = false
      if (saveBtn) {
        saveBtn.disabled = false
        saveBtn.textContent = 'Save Changes'
      }
    }
  }

  /**
   * Calculate ability modifier from score
   */
  calculateModifier(score) {
    return Math.floor((score - 10) / 2)
  }

  /**
   * Format date string
   */
  formatDate(dateString) {
    if (!dateString) return 'Unknown'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  /**
   * Handle close action
   */
  handleClose() {
    if (this.editMode) {
      const hasChanges = Object.keys(this.pendingChanges).length > 0
      if (hasChanges) {
        if (!confirm('You have unsaved changes. Are you sure you want to close?')) {
          return
        }
      }
    }
    
    this.hide()
    if (this.onClose) {
      this.onClose()
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

