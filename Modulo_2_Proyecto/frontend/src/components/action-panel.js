/**
 * ActionPanel Component
 *
 * Contextual panel that appears during the player's turn in combat.
 * Provides action options (Attack, Cast Spell, etc.), bonus actions,
 * movement tracking, target selection, and dice rolling interface.
 */

import { escapeHtml } from '../utils/index.js'

const CONTAINER_ID = 'action-panel-container'

// Standard D&D 5e actions available to all characters
const STANDARD_ACTIONS = [
  { id: 'attack', name: 'Attack', icon: '⚔️', description: 'Make a weapon attack' },
  { id: 'cast_spell', name: 'Cast Spell', icon: '✨', description: 'Cast a spell' },
  { id: 'dash', name: 'Dash', icon: '🏃', description: 'Double your movement speed' },
  { id: 'disengage', name: 'Disengage', icon: '🔙', description: 'Move without provoking attacks' },
  { id: 'dodge', name: 'Dodge', icon: '🛡️', description: 'Focus on avoiding attacks' },
  { id: 'help', name: 'Help', icon: '🤝', description: 'Aid an ally\'s next check' },
  { id: 'hide', name: 'Hide', icon: '🫥', description: 'Attempt to become hidden' },
  { id: 'ready', name: 'Ready', icon: '⏳', description: 'Prepare an action trigger' },
  { id: 'use_item', name: 'Use Item', icon: '🎒', description: 'Use an item from inventory' },
]

// Common bonus actions (class features would be added dynamically)
const STANDARD_BONUS_ACTIONS = [
  { id: 'offhand_attack', name: 'Off-hand Attack', icon: '🗡️', description: 'Attack with off-hand weapon' },
]

const ACTION_TYPES = {
  ACTION: 'action',
  BONUS_ACTION: 'bonus_action',
  REACTION: 'reaction',
  MOVEMENT: 'movement',
  FREE: 'free',
}

const PANEL_STATES = {
  HIDDEN: 'hidden',
  SELECTING_ACTION: 'selecting_action',
  SELECTING_TARGET: 'selecting_target',
  ROLLING_DICE: 'rolling_dice',
  CONFIRMING: 'confirming',
}

export class ActionPanel {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.encounterId - The active encounter ID
   * @param {number} options.characterId - The player's character ID
   * @param {Object} options.socketClient - SocketIO client instance
   * @param {number} options.gameId - The game ID
   * @param {Object} options.characterData - Character data with abilities, spells, features
   * @param {Function} options.onActionSubmitted - Callback when action is submitted
   * @param {Function} options.onTargetHighlight - Callback to highlight targets in CombatTracker
   * @param {Function} options.getCombatants - Function to get current combatants list
   */
  constructor(options) {
    this.encounterId = options.encounterId
    this.characterId = options.characterId
    this.socketClient = options.socketClient
    this.gameId = options.gameId
    this.characterData = options.characterData || {}
    this.onActionSubmitted = options.onActionSubmitted || (() => {})
    this.onTargetHighlight = options.onTargetHighlight || (() => {})
    this.getCombatants = options.getCombatants || (() => [])

    this.isVisible = false
    this.isMyTurn = false
    this.panelState = PANEL_STATES.HIDDEN
    this.combatantState = null

    // Turn resources tracking
    this.actionUsed = false
    this.bonusActionUsed = false
    this.reactionUsed = false
    this.movementUsed = 0
    this.maxMovement = 30

    // Current action being built
    this.pendingAction = null
    this.selectedTarget = null

    // Timer
    this.turnTimeoutSeconds = null
    this.turnStartedAt = null
    this.timerInterval = null
  }

  /**
   * Initialize the action panel
   */
  init() {
    this.ensureContainerExists()
    this.registerSocketHandlers()
    this.hide()
  }

  /**
   * Cleanup resources
   */
  destroy() {
    this.unregisterSocketHandlers()
    this.stopTimer()
    const container = document.getElementById(CONTAINER_ID)
    if (container) {
      container.innerHTML = ''
      container.hidden = true
    }
  }

  /**
   * Ensure the container exists in the DOM
   */
  ensureContainerExists() {
    let container = document.getElementById(CONTAINER_ID)
    if (!container) {
      const gameContent = document.getElementById('game-content')
      if (gameContent) {
        const section = document.createElement('section')
        section.id = CONTAINER_ID
        section.className = 'game-section action-panel-section'
        const combatTracker = document.getElementById('combat-tracker-container')
        if (combatTracker) {
          combatTracker.insertAdjacentElement('afterend', section)
        } else {
          const chatSection = gameContent.querySelector('.chat-section')
          if (chatSection) {
            chatSection.insertAdjacentElement('beforebegin', section)
          } else {
            gameContent.appendChild(section)
          }
        }
      }
    }
  }

  /**
   * Register WebSocket event handlers
   */
  registerSocketHandlers() {
    if (!this.socketClient) return

    this.socketClient.on('turn_started', this.handleTurnStarted.bind(this))
    this.socketClient.on('combat_action_logged', this.handleActionLogged.bind(this))
    this.socketClient.on('encounter_ended', this.handleEncounterEnded.bind(this))
    this.socketClient.on('encounter_paused', this.handleEncounterPaused.bind(this))
  }

  /**
   * Unregister WebSocket event handlers
   */
  unregisterSocketHandlers() {
    if (!this.socketClient) return

    const events = [
      'turn_started',
      'combat_action_logged',
      'encounter_ended',
      'encounter_paused',
    ]

    events.forEach((event) => this.socketClient.off(event))
  }

  // =========================================================================
  // Socket Event Handlers
  // =========================================================================

  handleTurnStarted(data) {
    if (data.encounter_id !== this.encounterId) return

    const currentCombatantKey = data.current_combatant?.key
    const isMyTurn = currentCombatantKey === `CHARACTER_${this.characterId}`

    this.turnStartedAt = data.turn_started_at ? new Date(data.turn_started_at) : new Date()
    this.turnTimeoutSeconds = data.timeout_seconds || null

    if (data.combatants_state) {
      this.combatantState = data.combatants_state[`CHARACTER_${this.characterId}`] || null
    }

    if (isMyTurn) {
      this.isMyTurn = true
      this.resetTurnResources()
      this.show(data.combatants_state?.[currentCombatantKey])
    } else {
      this.isMyTurn = false
      this.hide()
    }
  }

  handleActionLogged(data) {
    if (data.encounter_id !== this.encounterId) return

    // Update state if the action was from this character
    if (data.log_entry?.actor_key === `CHARACTER_${this.characterId}`) {
      this.markResourceUsed(data.log_entry.action_type)
      this.renderResourceIndicators()
    }

    // Update combatant state if provided
    if (data.combatants_state) {
      this.combatantState = data.combatants_state[`CHARACTER_${this.characterId}`] || null
    }
  }

  handleEncounterEnded(data) {
    if (data.encounter_id !== this.encounterId) return
    this.hide()
  }

  handleEncounterPaused(data) {
    if (data.encounter_id !== this.encounterId) return
    this.disable()
  }

  // =========================================================================
  // Public Methods
  // =========================================================================

  /**
   * Show the action panel when it's the player's turn
   */
  show(combatantState) {
    this.combatantState = combatantState || this.combatantState
    this.isVisible = true
    this.panelState = PANEL_STATES.SELECTING_ACTION
    this.loadCharacterActions()
    this.render()
    this.startTimer()

    const container = document.getElementById(CONTAINER_ID)
    if (container) container.hidden = false
  }

  /**
   * Hide the action panel
   */
  hide() {
    this.isVisible = false
    this.panelState = PANEL_STATES.HIDDEN
    this.stopTimer()
    this.clearSelection()

    const container = document.getElementById(CONTAINER_ID)
    if (container) container.hidden = true
  }

  /**
   * Disable interactions (when paused)
   */
  disable() {
    const container = document.getElementById(CONTAINER_ID)
    if (container) {
      container.classList.add('ap-disabled')
    }
    this.stopTimer()
  }

  /**
   * Re-enable interactions
   */
  enable() {
    const container = document.getElementById(CONTAINER_ID)
    if (container) {
      container.classList.remove('ap-disabled')
    }
    this.startTimer()
  }

  /**
   * Update character data (when features/spells change)
   */
  updateCharacterData(characterData) {
    this.characterData = characterData
    if (this.isVisible) {
      this.loadCharacterActions()
      this.render()
    }
  }

  // =========================================================================
  // Action Loading
  // =========================================================================

  loadCharacterActions() {
    // Load character-specific actions from characterData
    this.availableActions = [...STANDARD_ACTIONS]
    this.availableBonusActions = [...STANDARD_BONUS_ACTIONS]

    // Add class features that are actions
    const features = this.characterData.features || []
    features.forEach((feature) => {
      if (feature.action_type === 'action') {
        this.availableActions.push({
          id: `feature_${feature.id}`,
          name: feature.name,
          icon: feature.icon || '⚡',
          description: feature.description || '',
          isFeature: true,
        })
      } else if (feature.action_type === 'bonus_action') {
        this.availableBonusActions.push({
          id: `feature_${feature.id}`,
          name: feature.name,
          icon: feature.icon || '⚡',
          description: feature.description || '',
          isFeature: true,
        })
      }
    })

    // Load max movement from character data
    this.maxMovement = this.characterData.speed || 30
  }

  // =========================================================================
  // Rendering
  // =========================================================================

  render() {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    container.innerHTML = `
      <div class="ap-wrapper">
        ${this.renderHeader()}
        <div class="ap-body">
          ${this.renderActionSection()}
          ${this.renderBonusActionSection()}
          ${this.renderMovementSection()}
        </div>
        ${this.renderFooter()}
      </div>
      ${this.renderTargetOverlay()}
      ${this.renderRollDialog()}
    `

    this.setupEventListeners()
  }

  renderHeader() {
    return `
      <div class="ap-header">
        <div class="ap-header-left">
          <div class="ap-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="ap-title-section">
            <h2 class="ap-title">Your Turn</h2>
            <span class="ap-subtitle">Choose your action</span>
          </div>
        </div>
        <div class="ap-header-right">
          ${this.renderTimer()}
          ${this.renderResourceIndicators()}
        </div>
      </div>
    `
  }

  renderTimer() {
    if (!this.turnTimeoutSeconds) {
      return ''
    }

    return `
      <div class="ap-timer" id="ap-timer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
        <span class="ap-timer-value" id="ap-timer-value">--:--</span>
      </div>
    `
  }

  renderResourceIndicators() {
    return `
      <div class="ap-resources" id="ap-resources">
        <div class="ap-resource ${this.actionUsed ? 'ap-resource-used' : ''}" title="Action">
          <span class="ap-resource-icon">⚔️</span>
          <span class="ap-resource-label">Action</span>
        </div>
        <div class="ap-resource ${this.bonusActionUsed ? 'ap-resource-used' : ''}" title="Bonus Action">
          <span class="ap-resource-icon">⚡</span>
          <span class="ap-resource-label">Bonus</span>
        </div>
        <div class="ap-resource ${this.reactionUsed ? 'ap-resource-used' : ''}" title="Reaction">
          <span class="ap-resource-icon">🔄</span>
          <span class="ap-resource-label">Reaction</span>
        </div>
      </div>
    `
  }

  renderActionSection() {
    const isDisabled = this.actionUsed

    return `
      <div class="ap-section ${isDisabled ? 'ap-section-disabled' : ''}">
        <div class="ap-section-header">
          <h3 class="ap-section-title">Action</h3>
          ${isDisabled ? '<span class="ap-section-badge">Used</span>' : ''}
        </div>
        <div class="ap-action-grid">
          ${this.availableActions.map((action) => this.renderActionButton(action, isDisabled)).join('')}
        </div>
      </div>
    `
  }

  renderBonusActionSection() {
    const isDisabled = this.bonusActionUsed
    const hasBonusActions = this.availableBonusActions.length > 0

    if (!hasBonusActions) {
      return `
        <div class="ap-section ap-section-empty">
          <div class="ap-section-header">
            <h3 class="ap-section-title">Bonus Action</h3>
          </div>
          <p class="ap-empty-text">No bonus actions available</p>
        </div>
      `
    }

    return `
      <div class="ap-section ${isDisabled ? 'ap-section-disabled' : ''}">
        <div class="ap-section-header">
          <h3 class="ap-section-title">Bonus Action</h3>
          ${isDisabled ? '<span class="ap-section-badge">Used</span>' : ''}
        </div>
        <div class="ap-action-grid ap-action-grid-small">
          ${this.availableBonusActions.map((action) => this.renderActionButton(action, isDisabled, 'bonus_action')).join('')}
        </div>
      </div>
    `
  }

  renderMovementSection() {
    const remaining = this.maxMovement - this.movementUsed
    const percentUsed = (this.movementUsed / this.maxMovement) * 100

    return `
      <div class="ap-section ap-section-movement">
        <div class="ap-section-header">
          <h3 class="ap-section-title">Movement</h3>
          <span class="ap-movement-value">${remaining} / ${this.maxMovement} ft</span>
        </div>
        <div class="ap-movement-bar-container">
          <div class="ap-movement-bar" style="width: ${100 - percentUsed}%"></div>
        </div>
        <div class="ap-movement-controls">
          <button class="btn ap-btn-movement" data-movement="5" ${remaining < 5 ? 'disabled' : ''}>
            +5 ft
          </button>
          <button class="btn ap-btn-movement" data-movement="10" ${remaining < 10 ? 'disabled' : ''}>
            +10 ft
          </button>
          <button class="btn ap-btn-movement" data-movement="15" ${remaining < 15 ? 'disabled' : ''}>
            +15 ft
          </button>
          <button class="btn ap-btn-movement-reset" id="ap-reset-movement" ${this.movementUsed === 0 ? 'disabled' : ''}>
            Reset
          </button>
        </div>
      </div>
    `
  }

  renderActionButton(action, isDisabled, actionType = 'action') {
    return `
      <button 
        class="ap-action-btn ${isDisabled ? 'ap-action-btn-disabled' : ''}"
        data-action-id="${action.id}"
        data-action-type="${actionType}"
        ${isDisabled ? 'disabled' : ''}
        title="${escapeHtml(action.description)}"
      >
        <span class="ap-action-icon">${action.icon}</span>
        <span class="ap-action-name">${escapeHtml(action.name)}</span>
      </button>
    `
  }

  renderFooter() {
    return `
      <div class="ap-footer">
        <button class="btn ap-btn-end-turn" id="ap-end-turn-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
          End Turn
        </button>
      </div>
    `
  }

  renderTargetOverlay() {
    return `
      <div class="ap-target-overlay" id="ap-target-overlay" hidden>
        <div class="ap-target-content">
          <div class="ap-target-header">
            <h3>Select Target</h3>
            <button class="ap-target-close" id="ap-target-close">×</button>
          </div>
          <div class="ap-target-list" id="ap-target-list">
            <!-- Populated dynamically -->
          </div>
          <div class="ap-target-footer">
            <button class="btn ap-btn-cancel" id="ap-target-cancel">Cancel</button>
          </div>
        </div>
      </div>
    `
  }

  renderRollDialog() {
    return `
      <div class="ap-roll-dialog" id="ap-roll-dialog" hidden>
        <div class="ap-roll-content">
          <div class="ap-roll-header">
            <h3 id="ap-roll-title">Roll Dice</h3>
          </div>
          <div class="ap-roll-body">
            <div class="ap-roll-dice">
              <span class="ap-roll-dice-icon">🎲</span>
              <span class="ap-roll-dice-type" id="ap-roll-dice-type">d20</span>
            </div>
            <div class="ap-roll-modifier" id="ap-roll-modifier">
              <span>Modifier: </span>
              <span id="ap-roll-mod-value">+0</span>
            </div>
          </div>
          <div class="ap-roll-actions">
            <button class="btn ap-btn-roll" id="ap-roll-btn">
              Roll
            </button>
            <button class="btn ap-btn-cancel" id="ap-roll-cancel">Cancel</button>
          </div>
          <div class="ap-roll-result" id="ap-roll-result" hidden>
            <span class="ap-roll-result-value" id="ap-roll-result-value">15</span>
            <span class="ap-roll-result-total" id="ap-roll-result-total">Total: 18</span>
          </div>
        </div>
      </div>
    `
  }

  renderResourceIndicators() {
    return `
      <div class="ap-resources" id="ap-resources">
        <div class="ap-resource ${this.actionUsed ? 'ap-resource-used' : ''}" title="Action">
          <span class="ap-resource-icon">⚔️</span>
        </div>
        <div class="ap-resource ${this.bonusActionUsed ? 'ap-resource-used' : ''}" title="Bonus Action">
          <span class="ap-resource-icon">⚡</span>
        </div>
      </div>
    `
  }

  // =========================================================================
  // Event Handlers
  // =========================================================================

  setupEventListeners() {
    // Action buttons
    document.querySelectorAll('.ap-action-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => this.handleActionClick(e))
    })

    // Movement buttons
    document.querySelectorAll('.ap-btn-movement').forEach((btn) => {
      btn.addEventListener('click', (e) => this.handleMovementClick(e))
    })

    // Reset movement
    document.getElementById('ap-reset-movement')?.addEventListener('click', () => {
      this.movementUsed = 0
      this.render()
    })

    // End turn
    document.getElementById('ap-end-turn-btn')?.addEventListener('click', () => {
      this.endTurn()
    })

    // Target selection
    document.getElementById('ap-target-close')?.addEventListener('click', () => {
      this.closeTargetSelection()
    })
    document.getElementById('ap-target-cancel')?.addEventListener('click', () => {
      this.closeTargetSelection()
    })

    // Roll dialog
    document.getElementById('ap-roll-btn')?.addEventListener('click', () => {
      this.executeRoll()
    })
    document.getElementById('ap-roll-cancel')?.addEventListener('click', () => {
      this.closeRollDialog()
    })
  }

  handleActionClick(event) {
    const btn = event.currentTarget
    const actionId = btn.dataset.actionId
    const actionType = btn.dataset.actionType

    const action = actionType === 'bonus_action'
      ? this.availableBonusActions.find((a) => a.id === actionId)
      : this.availableActions.find((a) => a.id === actionId)

    if (!action) return

    this.pendingAction = {
      actionId,
      actionType,
      action,
    }

    // Actions that require a target
    if (['attack', 'cast_spell', 'help'].includes(actionId)) {
      this.openTargetSelection()
    } else {
      // Actions that don't need a target
      this.submitAction()
    }
  }

  handleMovementClick(event) {
    const distance = parseInt(event.currentTarget.dataset.movement, 10)
    const remaining = this.maxMovement - this.movementUsed

    if (distance <= remaining) {
      this.movementUsed += distance
      this.emitMovement(distance)
      this.render()
    }
  }

  // =========================================================================
  // Target Selection
  // =========================================================================

  openTargetSelection() {
    const overlay = document.getElementById('ap-target-overlay')
    const list = document.getElementById('ap-target-list')

    if (!overlay || !list) return

    const combatants = this.getCombatants()
    const isHostileAction = ['attack'].includes(this.pendingAction?.actionId)

    list.innerHTML = combatants
      .filter((c) => c.key !== `CHARACTER_${this.characterId}`)
      .filter((c) => {
        const state = c.state || {}
        return (state.current_hp ?? 1) > 0 // Filter out dead combatants
      })
      .map((combatant) => {
        const isHostile = combatant.participant_type === 'NPC' && combatant.npc_type === 'HOSTILE'
        const highlight = isHostileAction === isHostile ? 'ap-target-suggested' : ''

        return `
          <button 
            class="ap-target-item ${highlight}"
            data-target-key="${combatant.key}"
            data-target-name="${escapeHtml(combatant.name)}"
          >
            <span class="ap-target-icon">${combatant.participant_type === 'CHARACTER' ? '⚔️' : '🗡️'}</span>
            <span class="ap-target-name">${escapeHtml(combatant.name)}</span>
            <span class="ap-target-hp">${combatant.state?.current_hp ?? '?'} HP</span>
          </button>
        `
      })
      .join('')

    // Setup target click handlers
    list.querySelectorAll('.ap-target-item').forEach((item) => {
      item.addEventListener('click', () => {
        this.selectedTarget = {
          key: item.dataset.targetKey,
          name: item.dataset.targetName,
        }
        this.closeTargetSelection()
        this.openRollDialog()
      })
    })

    overlay.hidden = false
    this.panelState = PANEL_STATES.SELECTING_TARGET
    this.onTargetHighlight(true)
  }

  closeTargetSelection() {
    const overlay = document.getElementById('ap-target-overlay')
    if (overlay) overlay.hidden = true

    this.panelState = PANEL_STATES.SELECTING_ACTION
    this.onTargetHighlight(false)
  }

  // =========================================================================
  // Roll Dialog
  // =========================================================================

  openRollDialog() {
    const dialog = document.getElementById('ap-roll-dialog')
    const title = document.getElementById('ap-roll-title')
    const modValue = document.getElementById('ap-roll-mod-value')
    const resultSection = document.getElementById('ap-roll-result')

    if (!dialog) return

    // Set roll context
    let rollTitle = 'Attack Roll'
    let modifier = this.characterData.attack_bonus || 0

    if (this.pendingAction?.actionId === 'cast_spell') {
      rollTitle = 'Spell Attack'
      modifier = this.characterData.spell_attack_bonus || 0
    }

    if (title) title.textContent = rollTitle
    if (modValue) modValue.textContent = modifier >= 0 ? `+${modifier}` : modifier
    if (resultSection) resultSection.hidden = true

    dialog.hidden = false
    this.panelState = PANEL_STATES.ROLLING_DICE
  }

  closeRollDialog() {
    const dialog = document.getElementById('ap-roll-dialog')
    if (dialog) dialog.hidden = true

    this.pendingAction = null
    this.selectedTarget = null
    this.panelState = PANEL_STATES.SELECTING_ACTION
  }

  executeRoll() {
    const result = Math.floor(Math.random() * 20) + 1
    const modifier = this.characterData.attack_bonus || 0
    const total = result + modifier

    const resultSection = document.getElementById('ap-roll-result')
    const resultValue = document.getElementById('ap-roll-result-value')
    const resultTotal = document.getElementById('ap-roll-result-total')
    const rollBtn = document.getElementById('ap-roll-btn')

    if (resultSection) resultSection.hidden = false
    if (resultValue) {
      resultValue.textContent = result
      resultValue.classList.toggle('ap-roll-crit', result === 20)
      resultValue.classList.toggle('ap-roll-fail', result === 1)
    }
    if (resultTotal) resultTotal.textContent = `Total: ${total}`
    if (rollBtn) {
      rollBtn.textContent = 'Confirm'
      rollBtn.onclick = () => {
        this.submitAction({
          roll: result,
          total,
          modifier,
        })
      }
    }
  }

  // =========================================================================
  // Action Submission
  // =========================================================================

  submitAction(rollData = null) {
    if (!this.pendingAction) return

    const actionData = {
      encounter_id: this.encounterId,
      action_type: this.mapActionType(this.pendingAction.actionId),
      actor_key: `CHARACTER_${this.characterId}`,
      target_key: this.selectedTarget?.key || null,
      data: {
        action_name: this.pendingAction.action.name,
        roll: rollData?.roll || null,
        total: rollData?.total || null,
        modifier: rollData?.modifier || null,
      },
    }

    this.emitCombatAction(actionData)

    // Mark resource as used
    if (this.pendingAction.actionType === 'action') {
      this.actionUsed = true
    } else if (this.pendingAction.actionType === 'bonus_action') {
      this.bonusActionUsed = true
    }

    // Cleanup and re-render
    this.closeRollDialog()
    this.clearSelection()
    this.render()

    this.onActionSubmitted(actionData)
  }

  mapActionType(actionId) {
    const mapping = {
      attack: 'ATTACK',
      cast_spell: 'SPELL',
      dash: 'MOVEMENT',
      disengage: 'ABILITY',
      dodge: 'ABILITY',
      help: 'ABILITY',
      hide: 'ABILITY',
      ready: 'ABILITY',
      use_item: 'ABILITY',
      offhand_attack: 'ATTACK',
    }
    return mapping[actionId] || 'CUSTOM'
  }

  markResourceUsed(actionType) {
    if (['ATTACK', 'SPELL', 'ABILITY'].includes(actionType)) {
      // Check if it was a bonus action based on context
      // For now, mark action as used for main action types
      this.actionUsed = true
    }
  }

  // =========================================================================
  // Socket Emissions
  // =========================================================================

  emitCombatAction(actionData) {
    if (!this.socketClient?.socket) return

    this.socketClient.socket.emit('combat_action', actionData)
  }

  emitMovement(distance) {
    if (!this.socketClient?.socket) return

    this.socketClient.socket.emit('combat_action', {
      encounter_id: this.encounterId,
      action_type: 'MOVEMENT',
      actor_key: `CHARACTER_${this.characterId}`,
      data: {
        distance,
      },
    })
  }

  endTurn() {
    if (!this.socketClient?.socket) return

    this.socketClient.socket.emit('end_turn', {
      encounter_id: this.encounterId,
    })

    this.hide()
  }

  // =========================================================================
  // Timer
  // =========================================================================

  startTimer() {
    this.stopTimer()

    if (!this.turnTimeoutSeconds || !this.turnStartedAt) return

    const timerEl = document.getElementById('ap-timer')
    const timerValue = document.getElementById('ap-timer-value')

    if (!timerEl || !timerValue) return

    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.turnStartedAt.getTime()) / 1000)
      const remaining = Math.max(0, this.turnTimeoutSeconds - elapsed)

      const minutes = Math.floor(remaining / 60)
      const seconds = remaining % 60
      timerValue.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`

      timerEl.classList.toggle('ap-timer-warning', remaining <= 30)
      timerEl.classList.toggle('ap-timer-critical', remaining <= 10)

      if (remaining <= 0) {
        this.stopTimer()
      }
    }, 1000)
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval)
      this.timerInterval = null
    }
  }

  // =========================================================================
  // Utility Methods
  // =========================================================================

  resetTurnResources() {
    this.actionUsed = false
    this.bonusActionUsed = false
    this.reactionUsed = false
    this.movementUsed = 0
    this.pendingAction = null
    this.selectedTarget = null
  }

  clearSelection() {
    this.pendingAction = null
    this.selectedTarget = null
  }
}

