/**
 * GameCreator Component
 * 
 * A modal component for creating new games with customizable rules.
 * Supports selecting ruleset templates and configuring character/combat rules.
 */

import modalTemplate from './game-creator.html?raw'
import { MODAL_ID, DEFAULT_RULES, CUSTOM_TEMPLATE_ID } from './constants.js'
import { loadingTemplate, renderFullForm } from './templates.js'
import { fetchWithAuth } from '../../utils/index.js'
import { getUserFromToken } from '../../infrastructure/auth/auth.js'

export class GameCreator {
  /**
   * @param {Object} options - Configuration options
   * @param {Function} options.onSuccess - Callback when game is created successfully
   * @param {Function} options.onCancel - Callback when creation is cancelled
   */
  constructor(options) {
    this.onSuccess = options.onSuccess
    this.onCancel = options.onCancel

    this.templates = []
    this.selectedTemplateId = null
    this.isLoading = false
    this.isSubmitting = false
    this.error = null

    this.formData = {
      name: '',
      ...structuredClone(DEFAULT_RULES)
    }

    this.collapsibleStates = {
      character: true,
      combat: false
    }

    // Store original template rules to detect modifications
    this.originalTemplateRules = null

    this.boundHandleKeydown = this.handleKeydown.bind(this)
  }

  /**
   * Initialize and show the game creator modal
   */
  async init() {
    this.ensureModalExists()
    this.show()
    await this.loadTemplates()
  }

  /**
   * Ensure the modal container exists in the DOM
   */
  ensureModalExists() {
    if (!document.getElementById(MODAL_ID)) {
      document.body.insertAdjacentHTML('beforeend', modalTemplate)
    }
  }

  /**
   * Load available ruleset templates from the API
   */
  async loadTemplates() {
    const container = document.getElementById('gc-form-container')
    
    this.isLoading = true
    container.innerHTML = loadingTemplate()

    try {
      const response = await fetchWithAuth('/api/v1/ruleset-templates')
      
      if (response.ok) {
        this.templates = await response.json()
        
        // Select first template by default if available
        if (this.templates.length > 0 && this.selectedTemplateId === null) {
          const firstTemplate = this.templates[0]
          this.selectedTemplateId = firstTemplate.id
          
          // Apply and store original rules
          if (firstTemplate.base_rules) {
            this.applyTemplateRules(firstTemplate.base_rules)
            this.originalTemplateRules = structuredClone(firstTemplate.base_rules)
          }
        }
      } else {
        console.warn('[GameCreator] Could not load templates, using defaults')
        this.templates = []
      }
    } catch (error) {
      console.warn('[GameCreator] Error loading templates:', error)
      this.templates = []
    } finally {
      this.isLoading = false
      this.renderForm()
      this.setupEventListeners()
    }
  }

  /**
   * Render the complete form
   */
  renderForm() {
    const container = document.getElementById('gc-form-container')
    
    container.innerHTML = renderFullForm(this.formData, {
      templates: this.templates,
      selectedTemplateId: this.selectedTemplateId,
      error: this.error,
      collapsibleStates: this.collapsibleStates
    })
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    const modal = document.getElementById(MODAL_ID)
    const closeBtn = document.getElementById('gc-close-btn')
    const cancelBtn = document.getElementById('gc-cancel-btn')
    const submitBtn = document.getElementById('gc-submit-btn')

    closeBtn.addEventListener('click', () => this.handleCancel())
    cancelBtn.addEventListener('click', () => this.handleCancel())
    submitBtn.addEventListener('click', () => this.handleSubmit())

    modal.addEventListener('click', (event) => {
      if (event.target === modal) {
        this.handleCancel()
      }
    })

    document.addEventListener('keydown', this.boundHandleKeydown)

    this.setupFormListeners()
  }

  /**
   * Setup form-specific event listeners
   */
  setupFormListeners() {
    this.setupBasicInfoListeners()
    this.setupCollapsibleListeners()
    this.setupCharacterRulesListeners()
    this.setupCombatSettingsListeners()
  }

  /**
   * Setup basic info form listeners
   */
  setupBasicInfoListeners() {
    const nameInput = document.getElementById('gc-game-name')
    if (nameInput) {
      nameInput.addEventListener('input', (e) => {
        this.formData.name = e.target.value
      })
    }

    const templateSelect = document.getElementById('gc-template')
    if (templateSelect) {
      templateSelect.addEventListener('change', (e) => {
        this.handleTemplateChange(e.target.value)
      })
    }
  }

  /**
   * Setup collapsible section listeners
   */
  setupCollapsibleListeners() {
    document.querySelectorAll('.gc-collapsible-header').forEach(header => {
      header.addEventListener('click', () => {
        const section = header.parentElement.dataset.section
        this.toggleCollapsible(section)
      })
    })
  }

  /**
   * Setup character rules form listeners
   */
  setupCharacterRulesListeners() {
    this.setupCreationModeListener()
    this.setupLevelListeners()
    this.setupAttributeListeners()
    this.setupRacesListeners()
    this.setupClassesListeners()
    this.setupCharacterToggles()
  }

  setupCreationModeListener() {
    document.querySelectorAll('input[name="creation_mode"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.formData.character.creation_mode = e.target.value
      })
    })
  }

  setupLevelListeners() {
    const startLevel = document.getElementById('gc-start-level')
    if (startLevel) {
      startLevel.addEventListener('input', (e) => {
        this.formData.character.level.default = parseInt(e.target.value) || 1
      })
    }

    const maxLevel = document.getElementById('gc-max-level')
    if (maxLevel) {
      maxLevel.addEventListener('input', (e) => {
        this.formData.character.level.max = parseInt(e.target.value) || 20
      })
    }
  }

  setupAttributeListeners() {
    const attrMethod = document.getElementById('gc-attr-method')
    if (attrMethod) {
      attrMethod.addEventListener('change', (e) => {
        this.formData.character.attributes.method = e.target.value
        const pointBuyGroup = document.getElementById('gc-point-buy-group')
        if (pointBuyGroup) {
          pointBuyGroup.hidden = e.target.value !== 'point_buy'
        }
      })
    }

    const pointBuyTotal = document.getElementById('gc-point-buy-total')
    if (pointBuyTotal) {
      pointBuyTotal.addEventListener('input', (e) => {
        this.formData.character.attributes.point_buy.total_points = parseInt(e.target.value) || 27
      })
    }
  }

  setupRacesListeners() {
    const racesAllowAll = document.getElementById('gc-races-allow-all')
    if (racesAllowAll) {
      racesAllowAll.addEventListener('change', (e) => {
        this.formData.character.races.allow_all = e.target.checked
        const racesConfig = document.getElementById('gc-races-config')
        if (racesConfig) {
          racesConfig.hidden = e.target.checked
        }
      })
    }

    document.querySelectorAll('input[name="allowed_races"]').forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        this.formData.character.races.allowed = Array.from(
          document.querySelectorAll('input[name="allowed_races"]:checked')
        ).map(cb => cb.value)
      })
    })

    document.querySelectorAll('input[name="banned_races"]').forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        this.formData.character.races.banned = Array.from(
          document.querySelectorAll('input[name="banned_races"]:checked')
        ).map(cb => cb.value)
      })
    })
  }

  setupClassesListeners() {
    const classesAllowAll = document.getElementById('gc-classes-allow-all')
    if (classesAllowAll) {
      classesAllowAll.addEventListener('change', (e) => {
        this.formData.character.classes.allow_all = e.target.checked
        const classesConfig = document.getElementById('gc-classes-config')
        if (classesConfig) {
          classesConfig.hidden = e.target.checked
        }
      })
    }

    document.querySelectorAll('input[name="allowed_classes"]').forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        this.formData.character.classes.allowed = Array.from(
          document.querySelectorAll('input[name="allowed_classes"]:checked')
        ).map(cb => cb.value)
      })
    })

    document.querySelectorAll('input[name="banned_classes"]').forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        this.formData.character.classes.banned = Array.from(
          document.querySelectorAll('input[name="banned_classes"]:checked')
        ).map(cb => cb.value)
      })
    })
  }

  setupCharacterToggles() {
    const allowMulticlass = document.getElementById('gc-allow-multiclass')
    if (allowMulticlass) {
      allowMulticlass.addEventListener('change', (e) => {
        this.formData.character.classes.allow_multiclass = e.target.checked
      })
    }

    const backstoryRequired = document.getElementById('gc-backstory-required')
    if (backstoryRequired) {
      backstoryRequired.addEventListener('change', (e) => {
        this.formData.character.backstory.required = e.target.checked
      })
    }

    const customBackgrounds = document.getElementById('gc-custom-backgrounds')
    if (customBackgrounds) {
      customBackgrounds.addEventListener('change', (e) => {
        this.formData.character.allow_custom_backgrounds = e.target.checked
      })
    }
  }

  /**
   * Setup combat settings form listeners
   */
  setupCombatSettingsListeners() {
    this.setupTurnTimeoutListeners()
    this.setupDisconnectionListeners()
    this.setupCombatRulesListeners()
  }

  setupTurnTimeoutListeners() {
    const turnTimeout = document.getElementById('gc-turn-timeout')
    if (turnTimeout) {
      turnTimeout.addEventListener('change', (e) => {
        this.formData.combat.turn_timeout.enabled = e.target.checked
        const settings = document.getElementById('gc-timeout-settings')
        if (settings) {
          settings.hidden = !e.target.checked
        }
      })
    }

    const gracePeriod = document.getElementById('gc-grace-period')
    if (gracePeriod) {
      gracePeriod.addEventListener('input', (e) => {
        this.formData.combat.turn_timeout.grace_period_seconds = parseInt(e.target.value) || 60
      })
    }

    const maxWait = document.getElementById('gc-max-wait')
    if (maxWait) {
      maxWait.addEventListener('input', (e) => {
        this.formData.combat.turn_timeout.max_wait_seconds = parseInt(e.target.value) || 180
      })
    }

    const defaultAction = document.getElementById('gc-default-action')
    if (defaultAction) {
      defaultAction.addEventListener('change', (e) => {
        this.formData.combat.turn_timeout.default_action = e.target.value
      })
    }
  }

  setupDisconnectionListeners() {
    const showDisconnect = document.getElementById('gc-show-disconnect')
    if (showDisconnect) {
      showDisconnect.addEventListener('change', (e) => {
        this.formData.combat.disconnection.show_status_to_party = e.target.checked
      })
    }

    const dmControl = document.getElementById('gc-dm-control')
    if (dmControl) {
      dmControl.addEventListener('change', (e) => {
        this.formData.combat.disconnection.allow_dm_control = e.target.checked
      })
    }

    const autoPause = document.getElementById('gc-auto-pause')
    if (autoPause) {
      autoPause.addEventListener('change', (e) => {
        this.formData.combat.disconnection.auto_pause_on_disconnect = e.target.checked
      })
    }
  }

  setupCombatRulesListeners() {
    const flanking = document.getElementById('gc-flanking')
    if (flanking) {
      flanking.addEventListener('change', (e) => {
        this.formData.combat.flanking_gives_advantage = e.target.checked
      })
    }

    const criticalRule = document.getElementById('gc-critical-rule')
    if (criticalRule) {
      criticalRule.addEventListener('change', (e) => {
        this.formData.combat.critical_hit_rule = e.target.value
      })
    }
  }

  /**
   * Handle template selection change
   */
  handleTemplateChange(templateId) {
    this.selectedTemplateId = templateId ? parseInt(templateId) : null

    if (this.selectedTemplateId) {
      const template = this.templates.find(t => t.id === this.selectedTemplateId)
      if (template && template.base_rules) {
        this.applyTemplateRules(template.base_rules)
        // Store original rules to detect modifications later
        this.originalTemplateRules = structuredClone(template.base_rules)
      }
    } else {
      this.formData = {
        name: this.formData.name,
        ...structuredClone(DEFAULT_RULES)
      }
      this.originalTemplateRules = null
    }

    this.renderForm()
    this.setupFormListeners()
  }

  /**
   * Apply template rules to form data
   */
  applyTemplateRules(baseRules) {
    if (baseRules.character) {
      this.applyCharacterRules(baseRules.character)
    }

    if (baseRules.combat) {
      this.applyCombatRules(baseRules.combat)
    }
  }

  applyCharacterRules(charRules) {
    if (charRules.creation_mode) {
      this.formData.character.creation_mode = charRules.creation_mode
    }
    if (charRules.level) {
      Object.assign(this.formData.character.level, charRules.level)
    }
    if (charRules.attributes) {
      if (charRules.attributes.method) {
        this.formData.character.attributes.method = charRules.attributes.method
      }
      if (charRules.attributes.point_buy) {
        Object.assign(this.formData.character.attributes.point_buy, charRules.attributes.point_buy)
      }
    }
    if (charRules.races) {
      if (charRules.races.allow_all !== undefined) {
        this.formData.character.races.allow_all = charRules.races.allow_all
      }
      if (charRules.races.allowed) {
        this.formData.character.races.allowed = [...charRules.races.allowed]
      }
      if (charRules.races.banned) {
        this.formData.character.races.banned = [...charRules.races.banned]
      }
    }
    if (charRules.classes) {
      if (charRules.classes.allow_all !== undefined) {
        this.formData.character.classes.allow_all = charRules.classes.allow_all
      }
      if (charRules.classes.allowed) {
        this.formData.character.classes.allowed = [...charRules.classes.allowed]
      }
      if (charRules.classes.banned) {
        this.formData.character.classes.banned = [...charRules.classes.banned]
      }
      if (charRules.classes.allow_multiclass !== undefined) {
        this.formData.character.classes.allow_multiclass = charRules.classes.allow_multiclass
      }
    }
    if (charRules.backstory?.required !== undefined) {
      this.formData.character.backstory.required = charRules.backstory.required
    }
    if (charRules.allow_custom_backgrounds !== undefined) {
      this.formData.character.allow_custom_backgrounds = charRules.allow_custom_backgrounds
    }
  }

  applyCombatRules(combatRules) {
    if (combatRules.turn_timeout) {
      Object.assign(this.formData.combat.turn_timeout, combatRules.turn_timeout)
    }
    if (combatRules.disconnection) {
      Object.assign(this.formData.combat.disconnection, combatRules.disconnection)
    }
    if (combatRules.flanking_gives_advantage !== undefined) {
      this.formData.combat.flanking_gives_advantage = combatRules.flanking_gives_advantage
    }
    if (combatRules.critical_hit_rule) {
      this.formData.combat.critical_hit_rule = combatRules.critical_hit_rule
    }
  }

  /**
   * Toggle collapsible section
   */
  toggleCollapsible(section) {
    this.collapsibleStates[section] = !this.collapsibleStates[section]
    
    const element = document.querySelector(`.gc-collapsible[data-section="${section}"]`)
    if (element) {
      element.classList.toggle('is-open', this.collapsibleStates[section])
    }
  }

  /**
   * Handle keyboard events
   */
  handleKeydown(event) {
    if (event.key === 'Escape') {
      this.handleCancel()
    }
  }

  /**
   * Validate form data
   */
  validate() {
    const errors = []

    if (!this.formData.name || this.formData.name.trim().length < 3) {
      errors.push('Game name must be at least 3 characters')
    }

    if (this.formData.name && this.formData.name.length > 100) {
      errors.push('Game name must be less than 100 characters')
    }

    const { level } = this.formData.character
    if (level.default < 1 || level.default > 20) {
      errors.push('Starting level must be between 1 and 20')
    }

    if (level.max < level.default) {
      errors.push('Max level cannot be less than starting level')
    }

    const { turn_timeout } = this.formData.combat
    if (turn_timeout.enabled) {
      if (turn_timeout.grace_period_seconds < 10 || turn_timeout.grace_period_seconds > 300) {
        errors.push('Grace period must be between 10 and 300 seconds')
      }
      if (turn_timeout.max_wait_seconds < 30 || turn_timeout.max_wait_seconds > 600) {
        errors.push('Max wait time must be between 30 and 600 seconds')
      }
    }

    return errors
  }

  /**
   * Check if form rules were modified from the original template
   */
  hasRulesBeenModified() {
    // If Custom template selected, always consider it modified (needs custom_rules)
    if (this.selectedTemplateId === CUSTOM_TEMPLATE_ID) {
      return true
    }

    // If no original template stored, can't compare
    if (!this.originalTemplateRules) {
      return false
    }

    // Compare only the fields that the form can modify
    return this.compareFormFields()
  }

  /**
   * Compare form fields against original template values
   */
  compareFormFields() {
    const original = this.originalTemplateRules
    const current = this.formData

    // Character rules comparison
    if (original.character) {
      const origChar = original.character
      const currChar = current.character

      if (origChar.creation_mode !== currChar.creation_mode) return true
      if (origChar.level?.default !== currChar.level?.default) return true
      if (origChar.level?.max !== currChar.level?.max) return true
      if (origChar.attributes?.method !== currChar.attributes?.method) return true
      if (origChar.attributes?.point_buy?.total_points !== currChar.attributes?.point_buy?.total_points) return true
      if (origChar.races?.allow_all !== currChar.races?.allow_all) return true
      if (origChar.classes?.allow_all !== currChar.classes?.allow_all) return true
      if (origChar.classes?.allow_multiclass !== currChar.classes?.allow_multiclass) return true
      if (origChar.backstory?.required !== currChar.backstory?.required) return true
      if (origChar.allow_custom_backgrounds !== currChar.allow_custom_backgrounds) return true

      // Compare arrays
      if (!this.arraysEqual(origChar.races?.allowed || [], currChar.races?.allowed || [])) return true
      if (!this.arraysEqual(origChar.races?.banned || [], currChar.races?.banned || [])) return true
      if (!this.arraysEqual(origChar.classes?.allowed || [], currChar.classes?.allowed || [])) return true
      if (!this.arraysEqual(origChar.classes?.banned || [], currChar.classes?.banned || [])) return true
    }

    // Combat rules comparison
    if (original.combat) {
      const origCombat = original.combat
      const currCombat = current.combat

      if (origCombat.turn_timeout?.enabled !== currCombat.turn_timeout?.enabled) return true
      if (origCombat.turn_timeout?.grace_period_seconds !== currCombat.turn_timeout?.grace_period_seconds) return true
      if (origCombat.turn_timeout?.max_wait_seconds !== currCombat.turn_timeout?.max_wait_seconds) return true
      if (origCombat.turn_timeout?.default_action !== currCombat.turn_timeout?.default_action) return true
      if (origCombat.disconnection?.show_status_to_party !== currCombat.disconnection?.show_status_to_party) return true
      if (origCombat.disconnection?.allow_dm_control !== currCombat.disconnection?.allow_dm_control) return true
      if (origCombat.disconnection?.auto_pause_on_disconnect !== currCombat.disconnection?.auto_pause_on_disconnect) return true
      if (origCombat.flanking_gives_advantage !== currCombat.flanking_gives_advantage) return true
      if (origCombat.critical_hit_rule !== currCombat.critical_hit_rule) return true
    }

    return false
  }

  /**
   * Compare two arrays for equality (order-independent)
   */
  arraysEqual(arr1, arr2) {
    if (arr1.length !== arr2.length) return false
    const sorted1 = [...arr1].sort()
    const sorted2 = [...arr2].sort()
    return sorted1.every((val, idx) => val === sorted2[idx])
  }

  /**
   * Build custom_rules object for API
   */
  buildCustomRules() {
    return {
      version: '1.0',
      character: {
        creation_mode: this.formData.character.creation_mode,
        level: this.formData.character.level,
        attributes: {
          method: this.formData.character.attributes.method,
          point_buy: this.formData.character.attributes.point_buy
        },
        races: {
          allow_all: this.formData.character.races.allow_all,
          allowed: this.formData.character.races.allowed || [],
          banned: this.formData.character.races.banned || []
        },
        classes: {
          allow_all: this.formData.character.classes.allow_all,
          allowed: this.formData.character.classes.allowed || [],
          banned: this.formData.character.classes.banned || [],
          allow_multiclass: this.formData.character.classes.allow_multiclass
        },
        backstory: {
          required: this.formData.character.backstory.required,
          min_length: 0,
          max_length: 5000
        },
        allow_custom_backgrounds: this.formData.character.allow_custom_backgrounds
      },
      combat: {
        turn_timeout: this.formData.combat.turn_timeout,
        disconnection: this.formData.combat.disconnection,
        flanking_gives_advantage: this.formData.combat.flanking_gives_advantage,
        critical_hit_rule: this.formData.combat.critical_hit_rule
      }
    }
  }

  /**
   * Handle form submission
   */
  async handleSubmit() {
    const errors = this.validate()
    
    if (errors.length > 0) {
      this.error = errors[0]
      this.renderForm()
      this.setupFormListeners()
      return
    }

    this.error = null
    this.isSubmitting = true
    this.setSubmitLoading(true)

    try {
      const user = getUserFromToken()

      let customRules = null
      let templateIdToSend = this.selectedTemplateId

      // Check if rules were modified from original template
      const wasModified = this.hasRulesBeenModified()

      console.log('wasModified', wasModified)

      if (wasModified) {
        // If modified, treat as custom rules (send ID 3)
        customRules = this.buildCustomRules()
        templateIdToSend = CUSTOM_TEMPLATE_ID
      }

      const response = await fetchWithAuth('/api/v1/game/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.formData.name.trim(),
          dm_user_id: user.sub,
          custom_rules: customRules,
          ruleset_template_id: templateIdToSend
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to create game')
      }

      const result = await response.json()
      
      this.hide()
      
      if (this.onSuccess) {
        this.onSuccess(result)
      }
    } catch (error) {
      this.error = error.message
      this.renderForm()
      this.setupFormListeners()
    } finally {
      this.isSubmitting = false
      this.setSubmitLoading(false)
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
   * Set submit button loading state
   */
  setSubmitLoading(isLoading) {
    const submitBtn = document.getElementById('gc-submit-btn')
    if (!submitBtn) return

    const btnText = submitBtn.querySelector('.btn-text')
    const btnLoader = submitBtn.querySelector('.btn-loader')

    submitBtn.disabled = isLoading
    if (btnText) btnText.hidden = isLoading
    if (btnLoader) btnLoader.hidden = !isLoading
  }

  /**
   * Show the modal
   */
  show() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = false
      document.body.style.overflow = 'hidden'
      
      setTimeout(() => {
        const nameInput = document.getElementById('gc-game-name')
        if (nameInput) nameInput.focus()
      }, 100)
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
    document.removeEventListener('keydown', this.boundHandleKeydown)
  }

  /**
   * Destroy the component
   */
  destroy() {
    this.hide()
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.remove()
    }
  }
}

