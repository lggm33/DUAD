/**
 * CombatTracker Component
 *
 * Main panel during active combat showing initiative order, combatant states,
 * HP bars, conditions, and connection status. Receives real-time updates via WebSocket.
 */

import { fetchWithAuth, escapeHtml } from '../utils/index.js'

const CONTAINER_ID = 'combat-tracker-container'

const CONNECTION_STATUS = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  RECONNECTING: 'reconnecting',
}

const HP_THRESHOLDS = {
  HEALTHY: 50,
  WOUNDED: 25,
}

const CONDITION_ICONS = {
  blessed: '✨',
  poisoned: '☠️',
  stunned: '💫',
  frightened: '😨',
  charmed: '💕',
  paralyzed: '⚡',
  blinded: '👁️',
  deafened: '🔇',
  invisible: '👻',
  prone: '⬇️',
  restrained: '🔗',
  grappled: '✊',
  incapacitated: '💤',
  exhaustion: '😫',
  concentration: '🧠',
  default: '🔮',
}

const PARTICIPANT_ICONS = {
  CHARACTER: '⚔️',
  NPC_FRIENDLY: '🛡️',
  NPC_NEUTRAL: '👤',
  NPC_HOSTILE: '🗡️',
  NPC_MONSTER: '👹',
}

export class CombatTracker {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.encounterId - The active encounter ID
   * @param {Object} options.socketClient - SocketIO client instance
   * @param {number} options.gameId - The game ID
   * @param {string} options.currentUserRole - 'DM' or 'PLAYER'
   * @param {number|null} options.currentCharacterId - Current user's character ID (if player)
   * @param {Function} options.onTurnChange - Callback when turn changes
   * @param {Function} options.onEncounterEnd - Callback when encounter ends
   */
  constructor(options) {
    this.encounterId = options.encounterId
    this.socketClient = options.socketClient
    this.gameId = options.gameId
    this.currentUserRole = options.currentUserRole
    this.currentCharacterId = options.currentCharacterId
    this.onTurnChange = options.onTurnChange
    this.onEncounterEnd = options.onEncounterEnd

    this.state = null
    this.encounter = null
    this.isLoading = true
    this.error = null
    this.currentRound = 1
    this.currentTurnIndex = 0
    this.initiativeOrder = []
    this.combatantsState = {}
    this.turnStartedAt = null
    this.turnTimeoutSeconds = null
    this.timerInterval = null
  }

  /**
   * Initialize the combat tracker
   */
  async init() {
    this.ensureContainerExists()
    this.renderLoading()
    this.registerSocketHandlers()
    await this.loadEncounterState()
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
        section.className = 'game-section combat-tracker-section'
        const chatSection = gameContent.querySelector('.chat-section')
        if (chatSection) {
          chatSection.insertAdjacentElement('beforebegin', section)
        } else {
          gameContent.appendChild(section)
        }
      }
    }
  }

  /**
   * Load current encounter state from API
   */
  async loadEncounterState() {
    try {
      this.isLoading = true
      this.error = null
      this.renderLoading()

      const response = await fetchWithAuth(
        `/api/v1/game/${this.gameId}/encounter/${this.encounterId}/state`
      )

      if (!response.ok) {
        if (response.status === 404) {
          this.hide()
          return
        }
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to load encounter state')
      }

      const data = await response.json()
      this.updateFromStateData(data)
      this.isLoading = false
      this.render()
    } catch (error) {
      this.error = error.message
      this.isLoading = false
      this.renderError()
    }
  }

  /**
   * Update internal state from API/Socket data
   */
  updateFromStateData(data) {
    this.encounter = data.encounter || null
    this.state = data.state || null

    if (this.state) {
      this.currentRound = this.state.current_round || 1
      this.currentTurnIndex = this.state.current_turn_index || 0
      this.initiativeOrder = this.state.initiative_order || []
      this.combatantsState = this.state.combatants_state || {}
      this.turnStartedAt = this.state.turn_started_at
        ? new Date(this.state.turn_started_at)
        : null
    }
  }

  /**
   * Register WebSocket event handlers
   */
  registerSocketHandlers() {
    if (!this.socketClient) return

    this.socketClient.on('encounter_started', this.handleEncounterStarted.bind(this))
    this.socketClient.on('initiative_updated', this.handleInitiativeUpdated.bind(this))
    this.socketClient.on('combat_round_started', this.handleRoundStarted.bind(this))
    this.socketClient.on('turn_started', this.handleTurnStarted.bind(this))
    this.socketClient.on('turn_skipped', this.handleTurnSkipped.bind(this))
    this.socketClient.on('combatant_updated', this.handleCombatantUpdated.bind(this))
    this.socketClient.on('combat_action_logged', this.handleActionLogged.bind(this))
    this.socketClient.on('player_disconnected_combat', this.handlePlayerDisconnected.bind(this))
    this.socketClient.on('player_reconnected_combat', this.handlePlayerReconnected.bind(this))
    this.socketClient.on('encounter_paused', this.handleEncounterPaused.bind(this))
    this.socketClient.on('encounter_ended', this.handleEncounterEnded.bind(this))
    this.socketClient.on('encounter_state_sync', this.handleStateSync.bind(this))
  }

  /**
   * Unregister WebSocket event handlers
   */
  unregisterSocketHandlers() {
    if (!this.socketClient) return

    const events = [
      'encounter_started',
      'initiative_updated',
      'combat_round_started',
      'turn_started',
      'turn_skipped',
      'combatant_updated',
      'combat_action_logged',
      'player_disconnected_combat',
      'player_reconnected_combat',
      'encounter_paused',
      'encounter_ended',
      'encounter_state_sync',
    ]

    events.forEach((event) => this.socketClient.off(event))
  }

  // =========================================================================
  // Socket Event Handlers
  // =========================================================================

  handleEncounterStarted(data) {
    if (data.encounter_id !== this.encounterId) return
    this.loadEncounterState()
  }

  handleInitiativeUpdated(data) {
    if (data.encounter_id !== this.encounterId) return

    this.initiativeOrder = data.initiative_order || []
    this.renderInitiativeList()
  }

  handleRoundStarted(data) {
    if (data.encounter_id !== this.encounterId) return

    this.currentRound = data.round_number
    this.renderRoundIndicator()
  }

  handleTurnStarted(data) {
    if (data.encounter_id !== this.encounterId) return

    this.currentTurnIndex = data.current_turn_index ?? this.currentTurnIndex
    this.currentRound = data.round ?? this.currentRound
    this.turnStartedAt = data.turn_started_at ? new Date(data.turn_started_at) : new Date()
    this.turnTimeoutSeconds = data.timeout_seconds || null

    if (data.combatants_state) {
      this.combatantsState = data.combatants_state
    }

    this.renderInitiativeList()
    this.startTimer()

    if (this.onTurnChange) {
      const currentCombatant = this.getCurrentCombatant()
      this.onTurnChange(currentCombatant, this.isMyTurn())
    }
  }

  handleTurnSkipped(data) {
    if (data.encounter_id !== this.encounterId) return
    // Visual feedback handled by turn_started that follows
  }

  handleCombatantUpdated(data) {
    if (data.encounter_id !== this.encounterId) return

    const { combatant_key, changes } = data
    if (this.combatantsState[combatant_key]) {
      Object.assign(this.combatantsState[combatant_key], changes)
      this.renderCombatantCard(combatant_key)
    }
  }

  handleActionLogged(data) {
    if (data.encounter_id !== this.encounterId) return

    if (data.combatants_state) {
      this.combatantsState = data.combatants_state
      this.renderInitiativeList()
    }
  }

  handlePlayerDisconnected(data) {
    if (data.encounter_id !== this.encounterId) return

    const { combatant_key, grace_period_ends } = data
    if (this.combatantsState[combatant_key]) {
      this.combatantsState[combatant_key].connection_status = CONNECTION_STATUS.DISCONNECTED
      this.combatantsState[combatant_key].grace_period_ends = grace_period_ends
      this.renderCombatantCard(combatant_key)
    }
  }

  handlePlayerReconnected(data) {
    if (data.encounter_id !== this.encounterId) return

    const { combatant_key } = data
    if (this.combatantsState[combatant_key]) {
      this.combatantsState[combatant_key].connection_status = CONNECTION_STATUS.CONNECTED
      this.combatantsState[combatant_key].disconnected_at = null
      this.combatantsState[combatant_key].grace_period_ends = null
      this.renderCombatantCard(combatant_key)
    }
  }

  handleEncounterPaused(data) {
    if (data.encounter_id !== this.encounterId) return
    this.stopTimer()
    this.renderPausedOverlay(data.reason)
  }

  handleEncounterEnded(data) {
    if (data.encounter_id !== this.encounterId) return

    this.stopTimer()
    this.renderEndedState(data)

    if (this.onEncounterEnd) {
      this.onEncounterEnd(data)
    }
  }

  handleStateSync(data) {
    if (data.encounter?.id !== this.encounterId) return
    this.updateFromStateData(data)
    this.render()
  }

  // =========================================================================
  // Rendering Methods
  // =========================================================================

  /**
   * Render loading state
   */
  renderLoading() {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    container.hidden = false
    container.innerHTML = `
      <div class="ct-loading">
        <div class="ct-loading-spinner"></div>
        <p>Loading combat...</p>
      </div>
    `
  }

  /**
   * Render error state
   */
  renderError() {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    container.hidden = false
    container.innerHTML = `
      <div class="ct-error">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <h3>Failed to Load Combat</h3>
        <p>${escapeHtml(this.error)}</p>
        <button class="btn ct-btn-retry" id="ct-retry-btn">
          Try Again
        </button>
      </div>
    `

    document.getElementById('ct-retry-btn')?.addEventListener('click', () => this.loadEncounterState())
  }

  /**
   * Main render method
   */
  render() {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    container.hidden = false
    container.innerHTML = `
      <div class="ct-header">
        <div class="ct-header-left">
          <div class="ct-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.5 17.5L3 6V3h3l11.5 11.5"></path>
              <path d="M13 19l6-6"></path>
              <path d="M16 16l4 4"></path>
              <path d="M19 21a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"></path>
            </svg>
          </div>
          <div class="ct-title-section">
            <h2 class="ct-title">Combat</h2>
            <span class="ct-encounter-name">${escapeHtml(this.encounter?.name || 'Active Encounter')}</span>
          </div>
        </div>
        <div class="ct-header-right">
          ${this.renderRoundBadge()}
          ${this.renderTimer()}
        </div>
      </div>

      <div class="ct-body">
        <div class="ct-initiative-list" id="ct-initiative-list">
          ${this.renderInitiativeCards()}
        </div>
      </div>

      ${this.renderFooter()}
    `

    this.setupEventListeners()
    this.startTimer()
  }

  /**
   * Render round badge
   */
  renderRoundBadge() {
    return `
      <div class="ct-round-badge" id="ct-round-badge">
        <span class="ct-round-label">Round</span>
        <span class="ct-round-number">${this.currentRound}</span>
      </div>
    `
  }

  /**
   * Render timer display
   */
  renderTimer() {
    return `
      <div class="ct-timer" id="ct-timer" hidden>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
        <span class="ct-timer-value" id="ct-timer-value">--:--</span>
      </div>
    `
  }

  /**
   * Render all initiative cards
   */
  renderInitiativeCards() {
    if (this.initiativeOrder.length === 0) {
      return `
        <div class="ct-empty">
          <p>Waiting for initiative rolls...</p>
        </div>
      `
    }

    return this.initiativeOrder
      .map((combatant, index) => this.renderCombatantCardHtml(combatant, index))
      .join('')
  }

  /**
   * Render a single combatant card
   */
  renderCombatantCardHtml(combatant, index) {
    const isCurrentTurn = index === this.currentTurnIndex
    const state = this.combatantsState[combatant.key] || {}
    const isDead = state.current_hp !== undefined && state.current_hp <= 0
    const isDisconnected = state.connection_status === CONNECTION_STATUS.DISCONNECTED
    const isMyCharacter = this.isMyCharacter(combatant.key)

    const hpPercent = this.calculateHpPercent(state)
    const hpBarClass = this.getHpBarClass(hpPercent)
    const icon = this.getParticipantIcon(combatant)

    return `
      <div 
        class="ct-combatant-card ${isCurrentTurn ? 'ct-current-turn' : ''} ${isDead ? 'ct-dead' : ''} ${isMyCharacter ? 'ct-my-character' : ''}"
        data-combatant-key="${combatant.key}"
        id="ct-card-${combatant.key}"
      >
        <div class="ct-combatant-initiative">
          <span class="ct-initiative-value">${combatant.initiative ?? '?'}</span>
        </div>
        
        <div class="ct-combatant-icon">
          <span>${icon}</span>
        </div>
        
        <div class="ct-combatant-info">
          <div class="ct-combatant-name-row">
            <span class="ct-combatant-name">${escapeHtml(combatant.name || state.name || 'Unknown')}</span>
            ${isCurrentTurn ? '<span class="ct-turn-indicator">▶</span>' : ''}
            ${isDisconnected ? '<span class="ct-disconnected-badge">DISCONN</span>' : ''}
            ${isDead ? '<span class="ct-dead-badge">DEAD</span>' : ''}
          </div>
          
          <div class="ct-hp-section">
            <div class="ct-hp-bar-container">
              <div class="ct-hp-bar ${hpBarClass}" style="width: ${hpPercent}%"></div>
            </div>
            <span class="ct-hp-text">
              ${state.current_hp ?? '?'} / ${state.max_hp ?? '?'}
            </span>
          </div>
        </div>
        
        ${this.renderConditions(state.conditions || [])}
      </div>
    `
  }

  /**
   * Render conditions chips
   */
  renderConditions(conditions) {
    if (!conditions || conditions.length === 0) return ''

    const chips = conditions
      .slice(0, 3)
      .map((condition) => {
        const icon = CONDITION_ICONS[condition.toLowerCase()] || CONDITION_ICONS.default
        return `<span class="ct-condition-chip" title="${escapeHtml(condition)}">${icon}</span>`
      })
      .join('')

    const moreCount = conditions.length - 3
    const moreIndicator = moreCount > 0 ? `<span class="ct-condition-more">+${moreCount}</span>` : ''

    return `
      <div class="ct-conditions">
        ${chips}
        ${moreIndicator}
      </div>
    `
  }

  /**
   * Render footer with DM controls
   */
  renderFooter() {
    if (this.currentUserRole !== 'DM') {
      return `
        <div class="ct-footer ct-footer-player">
          ${this.isMyTurn() ? '<span class="ct-your-turn-text">⚔️ Your Turn!</span>' : ''}
        </div>
      `
    }

    return `
      <div class="ct-footer ct-footer-dm">
        <div class="ct-dm-controls">
          <button class="btn ct-btn-skip" id="ct-skip-turn-btn" title="Skip Turn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 4 15 12 5 20 5 4"></polygon>
              <line x1="19" y1="5" x2="19" y2="19"></line>
            </svg>
            Skip
          </button>
          <button class="btn ct-btn-next" id="ct-next-turn-btn" title="Next Turn">
            Next Turn
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
          <button class="btn ct-btn-pause" id="ct-pause-btn" title="Pause Combat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="4" width="4" height="16"></rect>
              <rect x="14" y="4" width="4" height="16"></rect>
            </svg>
          </button>
          <button class="btn ct-btn-end" id="ct-end-btn" title="End Encounter">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            </svg>
          </button>
        </div>
      </div>
    `
  }

  /**
   * Render paused overlay
   */
  renderPausedOverlay(reason) {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    const overlay = document.createElement('div')
    overlay.className = 'ct-paused-overlay'
    overlay.id = 'ct-paused-overlay'
    overlay.innerHTML = `
      <div class="ct-paused-content">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="6" y="4" width="4" height="16"></rect>
          <rect x="14" y="4" width="4" height="16"></rect>
        </svg>
        <h3>Combat Paused</h3>
        <p>${escapeHtml(reason || 'The DM has paused combat')}</p>
        ${this.currentUserRole === 'DM' ? `
          <button class="btn ct-btn-resume" id="ct-resume-btn">Resume Combat</button>
        ` : ''}
      </div>
    `

    container.appendChild(overlay)

    document.getElementById('ct-resume-btn')?.addEventListener('click', () => {
      this.emitResumeEncounter()
      overlay.remove()
    })
  }

  /**
   * Render ended state
   */
  renderEndedState(data) {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    const outcomeEmoji = {
      VICTORY: '🎉',
      DEFEAT: '💀',
      FLED: '🏃',
      NEGOTIATED: '🤝',
      ABORTED: '⏹️',
    }

    container.innerHTML = `
      <div class="ct-ended">
        <div class="ct-ended-icon">${outcomeEmoji[data.outcome] || '⚔️'}</div>
        <h3>Combat Ended</h3>
        <p class="ct-ended-outcome">${data.outcome}</p>
        ${data.summary ? `<p class="ct-ended-summary">${escapeHtml(JSON.stringify(data.summary))}</p>` : ''}
        <button class="btn ct-btn-close" id="ct-close-ended-btn">Close</button>
      </div>
    `

    document.getElementById('ct-close-ended-btn')?.addEventListener('click', () => {
      this.hide()
    })
  }

  /**
   * Re-render only the initiative list
   */
  renderInitiativeList() {
    const list = document.getElementById('ct-initiative-list')
    if (list) {
      list.innerHTML = this.renderInitiativeCards()
    }
  }

  /**
   * Re-render only the round indicator
   */
  renderRoundIndicator() {
    const badge = document.getElementById('ct-round-badge')
    if (badge) {
      badge.querySelector('.ct-round-number').textContent = this.currentRound
    }
  }

  /**
   * Re-render a single combatant card
   */
  renderCombatantCard(combatantKey) {
    const card = document.getElementById(`ct-card-${combatantKey}`)
    if (!card) return

    const index = this.initiativeOrder.findIndex((c) => c.key === combatantKey)
    if (index === -1) return

    const combatant = this.initiativeOrder[index]
    const newHtml = this.renderCombatantCardHtml(combatant, index)

    const temp = document.createElement('div')
    temp.innerHTML = newHtml
    card.replaceWith(temp.firstElementChild)
  }

  // =========================================================================
  // Timer Methods
  // =========================================================================

  startTimer() {
    this.stopTimer()

    if (!this.turnTimeoutSeconds || !this.turnStartedAt) {
      const timerEl = document.getElementById('ct-timer')
      if (timerEl) timerEl.hidden = true
      return
    }

    const timerEl = document.getElementById('ct-timer')
    const timerValue = document.getElementById('ct-timer-value')
    if (!timerEl || !timerValue) return

    timerEl.hidden = false

    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.turnStartedAt.getTime()) / 1000)
      const remaining = Math.max(0, this.turnTimeoutSeconds - elapsed)

      const minutes = Math.floor(remaining / 60)
      const seconds = remaining % 60
      timerValue.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`

      timerEl.classList.toggle('ct-timer-warning', remaining <= 30)
      timerEl.classList.toggle('ct-timer-critical', remaining <= 10)

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
  // Event Handlers
  // =========================================================================

  setupEventListeners() {
    document.getElementById('ct-next-turn-btn')?.addEventListener('click', () => {
      this.emitNextTurn()
    })

    document.getElementById('ct-skip-turn-btn')?.addEventListener('click', () => {
      this.emitSkipTurn()
    })

    document.getElementById('ct-pause-btn')?.addEventListener('click', () => {
      this.emitPauseEncounter()
    })

    document.getElementById('ct-end-btn')?.addEventListener('click', () => {
      this.showEndEncounterDialog()
    })
  }

  // =========================================================================
  // Socket Emit Methods
  // =========================================================================

  emitNextTurn() {
    if (!this.socketClient) return
    this.socketClient.socket?.emit('next_turn', { encounter_id: this.encounterId })
  }

  emitSkipTurn() {
    if (!this.socketClient) return
    this.socketClient.socket?.emit('skip_turn', {
      encounter_id: this.encounterId,
      reason: 'dm_skip',
    })
  }

  emitPauseEncounter() {
    if (!this.socketClient) return
    this.socketClient.socket?.emit('pause_encounter', { encounter_id: this.encounterId })
  }

  emitResumeEncounter() {
    if (!this.socketClient) return
    this.socketClient.socket?.emit('resume_encounter', { encounter_id: this.encounterId })
  }

  emitEndEncounter(outcome) {
    if (!this.socketClient) return
    this.socketClient.socket?.emit('end_encounter', {
      encounter_id: this.encounterId,
      outcome,
    })
  }

  showEndEncounterDialog() {
    const outcomes = ['VICTORY', 'DEFEAT', 'FLED', 'NEGOTIATED', 'ABORTED']

    const dialog = document.createElement('div')
    dialog.className = 'ct-end-dialog-overlay'
    dialog.innerHTML = `
      <div class="ct-end-dialog">
        <h3>End Encounter</h3>
        <p>Select the outcome:</p>
        <div class="ct-outcome-buttons">
          ${outcomes.map((o) => `<button class="btn ct-outcome-btn" data-outcome="${o}">${o}</button>`).join('')}
        </div>
        <button class="btn ct-btn-cancel" id="ct-cancel-end">Cancel</button>
      </div>
    `

    document.body.appendChild(dialog)

    dialog.querySelectorAll('.ct-outcome-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.emitEndEncounter(btn.dataset.outcome)
        dialog.remove()
      })
    })

    document.getElementById('ct-cancel-end')?.addEventListener('click', () => {
      dialog.remove()
    })

    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) dialog.remove()
    })
  }

  // =========================================================================
  // Utility Methods
  // =========================================================================

  getCurrentCombatant() {
    return this.initiativeOrder[this.currentTurnIndex] || null
  }

  isMyTurn() {
    const current = this.getCurrentCombatant()
    if (!current) return false

    if (this.currentUserRole === 'DM') {
      return current.participant_type === 'NPC'
    }

    return current.key === `CHARACTER_${this.currentCharacterId}`
  }

  isMyCharacter(combatantKey) {
    return combatantKey === `CHARACTER_${this.currentCharacterId}`
  }

  calculateHpPercent(state) {
    if (!state.max_hp || state.max_hp <= 0) return 100
    const current = state.current_hp ?? state.max_hp
    return Math.min(100, Math.max(0, (current / state.max_hp) * 100))
  }

  getHpBarClass(percent) {
    if (percent > HP_THRESHOLDS.HEALTHY) return 'ct-hp-healthy'
    if (percent > HP_THRESHOLDS.WOUNDED) return 'ct-hp-wounded'
    return 'ct-hp-critical'
  }

  getParticipantIcon(combatant) {
    if (combatant.participant_type === 'CHARACTER') {
      return PARTICIPANT_ICONS.CHARACTER
    }

    const npcType = combatant.npc_type || 'HOSTILE'
    return PARTICIPANT_ICONS[`NPC_${npcType}`] || PARTICIPANT_ICONS.NPC_HOSTILE
  }

  show() {
    const container = document.getElementById(CONTAINER_ID)
    if (container) container.hidden = false
  }

  hide() {
    const container = document.getElementById(CONTAINER_ID)
    if (container) container.hidden = true
  }

  /**
   * Request state sync from server
   */
  syncState() {
    if (!this.socketClient) return
    this.socketClient.socket?.emit('sync_encounter_state', { encounter_id: this.encounterId })
  }
}

