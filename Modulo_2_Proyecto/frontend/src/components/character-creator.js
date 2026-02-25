/**
 * CharacterCreator Component
 * 
 * A dynamic form component that generates character creation fields
 * based on the game's ruleset. Supports point-buy stats, skill selection,
 * and validation according to the game rules.
 */

import { fetchWithAuth } from '../utils/index.js'
import { 
  MODAL_ID,
  STAT_MIN,
  STAT_MAX,
  DEFAULT_POINT_BUY_TOTAL,
  DEFAULT_SKILL_COUNT
} from './character-creator-constants.js'
import {
  recalculatePoints,
  validateCharacter,
  buildPayload
} from './character-creator-utils.js'
import {
  getModalTemplate,
  renderValidationSummary,
  renderBasicInfoSection,
  renderStatsSection,
  renderSkillsSection,
  renderDescriptionSection,
  renderPreviewCard
} from './character-creator-templates.js'
import {
  updateStatDisplay,
  updatePointsDisplay,
  updateSkillsDisplay,
  updatePreview
} from './character-creator-dom.js'

export class CharacterCreator {
  constructor(options) {
    this.gameId = options.gameId
    this.characterId = options.characterId || null
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
    this.isEditMode = !!this.characterId
  }

  init() {
    this.ensureModalExists()
    this.renderForm()
    this.setupEventListeners()
    updatePointsDisplay(this.pointsUsed, this.maxPoints)
    this.show()
  }

  ensureModalExists() {
    if (!document.getElementById(MODAL_ID)) {
      document.body.insertAdjacentHTML('beforeend', getModalTemplate())
    }
  }

  renderForm() {
    const container = document.getElementById('cc-form-container')
    if (!container) return

    container.innerHTML = `
      ${renderValidationSummary(this.errors)}
      ${renderBasicInfoSection(this.characterData, this.rules)}
      ${renderStatsSection(this.characterData.stats, this.pointsUsed, this.maxPoints)}
      ${renderSkillsSection(this.rules.skills, this.characterData.skills, this.maxSkills)}
      ${renderDescriptionSection(this.characterData.description)}
      ${renderPreviewCard(this.characterData)}
    `
  }

  setupEventListeners() {
    const modal = document.getElementById(MODAL_ID)
    if (!modal) return

    const closeBtn = document.getElementById('cc-close-btn')
    closeBtn?.addEventListener('click', () => this.handleCancel())

    modal.addEventListener('click', (e) => {
      if (e.target === modal) this.handleCancel()
    })

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.hidden) {
        this.handleCancel()
      }
    })

    this.setupFormInputListeners()
    this.setupStatButtonListeners()
    this.setupSkillListeners()

    document.getElementById('cc-save-draft-btn')?.addEventListener('click', () => this.handleSaveDraft())
    document.getElementById('cc-submit-btn')?.addEventListener('click', () => this.handleSubmit())
  }

  setupFormInputListeners() {
    const nameInput = document.getElementById('cc-name')
    const raceSelect = document.getElementById('cc-race')
    const classSelect = document.getElementById('cc-class')
    const backgroundInput = document.getElementById('cc-background')
    const descriptionTextarea = document.getElementById('cc-description')

    nameInput?.addEventListener('input', (e) => {
      this.characterData.name = e.target.value
      updatePreview(this.characterData)
    })

    raceSelect?.addEventListener('change', (e) => {
      this.characterData.race = e.target.value
      updatePreview(this.characterData)
    })

    classSelect?.addEventListener('change', (e) => {
      this.characterData.class = e.target.value
      updatePreview(this.characterData)
    })

    backgroundInput?.addEventListener('input', (e) => {
      this.characterData.background = e.target.value
    })

    descriptionTextarea?.addEventListener('input', (e) => {
      this.characterData.description = e.target.value
    })
  }

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

  setupSkillListeners() {
    const skillItems = document.querySelectorAll('.cc-skill-item')
    skillItems.forEach(item => {
      item.addEventListener('click', () => {
        const skillName = item.dataset.skill
        this.handleSkillToggle(skillName)
      })
    })
  }

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
      this.pointsUsed = recalculatePoints(this.characterData.stats)
      updateStatDisplay(stat, newValue)
      updatePointsDisplay(this.pointsUsed, this.maxPoints)
      updatePreview(this.characterData)
    }
  }

  handleSkillToggle(skillName) {
    const index = this.characterData.skills.indexOf(skillName)
    if (index > -1) {
      this.characterData.skills.splice(index, 1)
    } else if (this.characterData.skills.length < this.maxSkills) {
      this.characterData.skills.push(skillName)
    }
    updateSkillsDisplay(this.characterData.skills, this.maxSkills)
  }

  validate() {
    this.errors = validateCharacter(
      this.characterData,
      this.pointsUsed,
      this.maxPoints,
      this.maxSkills
    )
    return this.errors.length === 0
  }

  async handleSaveDraft() {
    if (!this.characterData.name.trim()) {
      this.errors = ['Please enter a character name to save as draft']
      this.renderForm()
      this.setupFormInputListeners()
      this.setupStatButtonListeners()
      this.setupSkillListeners()
      return
    }

    try {
      const payload = buildPayload(this.characterData, false)
      
      let url, method
      if (this.isEditMode) {
        url = `/api/v1/game/${this.gameId}/character/${this.characterId}`
        method = 'PUT'
      } else {
        url = `/api/v1/game/${this.gameId}/character`
        method = 'POST'
      }

      const response = await fetchWithAuth(url, {
        method,
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
      const payload = buildPayload(this.characterData, true)
      
      let url, method
      if (this.isEditMode) {
        url = `/api/v1/game/${this.gameId}/character/${this.characterId}`
        method = 'PUT'
      } else {
        url = `/api/v1/game/${this.gameId}/character`
        method = 'POST'
      }

      const response = await fetchWithAuth(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to save character')
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

  handleCancel() {
    this.hide()
    if (this.onCancel) {
      this.onCancel()
    }
  }

  show() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = false
      document.body.style.overflow = 'hidden'
    }
  }

  hide() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = true
      document.body.style.overflow = ''
    }
  }

  destroy() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.remove()
    }
    document.body.style.overflow = ''
  }
}
