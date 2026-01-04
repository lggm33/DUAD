/**
 * Combat Log Component
 * Real-time feed of all combat actions during an encounter
 */

import { getAccessToken } from '../infrastructure/auth/auth.js'

// Action type icons and formatters
const ACTION_CONFIG = {
  INITIATIVE_ROLL: {
    icon: '🎲',
    format: (log) => `${log.actor_name} rolled ${log.data?.roll || '?'} for initiative`
  },
  ATTACK: {
    icon: '⚔️',
    format: (log) => {
      const hitMiss = log.result?.hit ? 'HIT' : 'MISS'
      const roll = log.result?.roll ? ` (${log.result.roll})` : ''
      return `${log.actor_name} attacks ${log.target_name || 'target'} - ${hitMiss}${roll}`
    }
  },
  DAMAGE: {
    icon: '💥',
    format: (log) => {
      const damageType = log.data?.damage_type || ''
      return `${log.target_name || 'Target'} takes ${log.data?.amount || '?'} ${damageType} damage`
    }
  },
  HEAL: {
    icon: '💚',
    format: (log) => `${log.target_name || log.actor_name} heals ${log.data?.amount || '?'} HP`
  },
  SPELL: {
    icon: '✨',
    format: (log) => `${log.actor_name} casts ${log.data?.spell_name || 'a spell'}`
  },
  ABILITY: {
    icon: '🔶',
    format: (log) => `${log.actor_name} uses ${log.data?.ability_name || 'an ability'}`
  },
  MOVEMENT: {
    icon: '🏃',
    format: (log) => `${log.actor_name} moves ${log.data?.distance || '?'} ft`
  },
  CONDITION_APPLY: {
    icon: '🔮',
    format: (log) => `${log.target_name || log.actor_name} is now ${log.data?.condition || 'affected'}`
  },
  CONDITION_REMOVE: {
    icon: '✖️',
    format: (log) => `${log.target_name || log.actor_name} is no longer ${log.data?.condition || 'affected'}`
  },
  DEATH: {
    icon: '💀',
    format: (log) => `${log.target_name || log.actor_name} has fallen!`
  },
  TURN_START: {
    icon: '➡️',
    format: (log) => `${log.actor_name}'s turn begins`
  },
  TURN_END: {
    icon: '⏹️',
    format: (log) => `${log.actor_name}'s turn ends`
  },
  TURN_SKIPPED: {
    icon: '⏭️',
    format: (log) => {
      const reason = log.data?.reason || 'unknown reason'
      return `${log.actor_name}'s turn was skipped: ${reason}`
    }
  },
  DM_OVERRIDE: {
    icon: '👑',
    format: (log) => `DM: ${log.data?.description || 'made a change'}`
  },
  CUSTOM: {
    icon: '📝',
    format: (log) => log.data?.description || 'Custom action'
  }
}

// Default config for unknown action types
const DEFAULT_ACTION_CONFIG = {
  icon: '📋',
  format: (log) => `${log.actor_name}: ${log.action_type}`
}

// Filter options for the combat log
const FILTER_OPTIONS = [
  { value: 'all', label: 'All Actions' },
  { value: 'combat', label: 'Combat Only' },
  { value: 'turns', label: 'Turns Only' },
  { value: 'damage', label: 'Damage & Healing' }
]

const FILTER_MAPPINGS = {
  all: null,
  combat: ['ATTACK', 'DAMAGE', 'SPELL', 'ABILITY'],
  turns: ['TURN_START', 'TURN_END', 'TURN_SKIPPED'],
  damage: ['DAMAGE', 'HEAL', 'DEATH']
}

/**
 * Combat Log - Shows real-time feed of combat actions
 */
export class CombatLog {
  constructor({ encounterId, gameId, socketClient, onError }) {
    this.encounterId = encounterId
    this.gameId = gameId
    this.socketClient = socketClient
    this.onError = onError || (() => {})
    
    this.logEntries = []
    this.currentFilter = 'all'
    this.isInitialized = false
    this.containerId = 'combat-log-container'
  }

  /**
   * Initialize the combat log
   */
  async init() {
    await this.loadLogHistory()
    this.registerSocketHandlers()
    this.setupFilterDropdown()
    this.isInitialized = true
  }

  /**
   * Load combat log history from the API
   */
  async loadLogHistory() {
    const loadingEl = document.getElementById('combat-log-loading')
    const emptyEl = document.getElementById('combat-log-empty')
    const listEl = document.getElementById('combat-log-list')

    if (!loadingEl || !listEl) {
      console.warn('[CombatLog] Required DOM elements not found')
      return
    }

    try {
      const url = `/api/v1/game/${this.gameId}/encounter/${this.encounterId}/logs?limit=50`
      const response = await this.fetchWithAuth(url)

      if (!response.ok) {
        throw new Error('Failed to load combat logs')
      }

      const logs = await response.json()
      
      loadingEl.hidden = true

      if (logs.length === 0) {
        emptyEl.hidden = false
      } else {
        emptyEl.hidden = true
        this.logEntries = logs
        this.renderLogs()
      }
    } catch (error) {
      console.error('[CombatLog] Failed to load history:', error)
      loadingEl.hidden = true
      emptyEl.hidden = false
      this.onError('Failed to load combat log')
    }
  }

  /**
   * Register WebSocket event handlers for real-time updates
   */
  registerSocketHandlers() {
    if (!this.socketClient) {
      console.warn('[CombatLog] No socket client provided')
      return
    }

    this.socketClient.on('combat_action_logged', this.handleCombatActionLogged.bind(this))
    this.socketClient.on('combat_round_started', this.handleRoundStarted.bind(this))
    this.socketClient.on('encounter_ended', this.handleEncounterEnded.bind(this))
  }

  /**
   * Handle new combat action logged event
   */
  handleCombatActionLogged(data) {
    const emptyEl = document.getElementById('combat-log-empty')
    if (emptyEl) {
      emptyEl.hidden = true
    }

    const logEntry = data.log_entry
    this.logEntries.push(logEntry)
    this.appendLogEntry(logEntry)
    this.scrollToBottom()
  }

  /**
   * Handle round started event
   */
  handleRoundStarted(data) {
    const roundEntry = {
      id: `round-${data.round_number}`,
      action_type: 'ROUND_START',
      actor_name: 'Combat',
      round_number: data.round_number,
      created_at: new Date().toISOString(),
      data: { round: data.round_number }
    }

    this.logEntries.push(roundEntry)
    this.appendRoundDivider(data.round_number)
    this.scrollToBottom()
  }

  /**
   * Handle encounter ended event
   */
  handleEncounterEnded(data) {
    const endEntry = {
      id: `end-${Date.now()}`,
      action_type: 'ENCOUNTER_END',
      actor_name: 'Combat',
      created_at: new Date().toISOString(),
      data: { outcome: data.outcome }
    }

    this.logEntries.push(endEntry)
    this.appendEncounterEnd(data)
    this.scrollToBottom()
  }

  /**
   * Setup filter dropdown functionality
   */
  setupFilterDropdown() {
    const filterBtn = document.getElementById('combat-log-filter-btn')
    const filterDropdown = document.getElementById('combat-log-filter-dropdown')

    if (!filterBtn || !filterDropdown) return

    filterBtn.addEventListener('click', (e) => {
      e.stopPropagation()
      filterDropdown.classList.toggle('is-open')
    })

    document.addEventListener('click', () => {
      filterDropdown.classList.remove('is-open')
    })

    filterDropdown.querySelectorAll('[data-filter]').forEach(option => {
      option.addEventListener('click', (e) => {
        const filter = e.target.dataset.filter
        this.setFilter(filter)
        filterDropdown.classList.remove('is-open')
        
        filterDropdown.querySelectorAll('[data-filter]').forEach(opt => {
          opt.classList.toggle('is-active', opt.dataset.filter === filter)
        })
      })
    })
  }

  /**
   * Set the current filter and re-render logs
   */
  setFilter(filter) {
    this.currentFilter = filter
    this.renderLogs()
  }

  /**
   * Get filtered log entries based on current filter
   */
  getFilteredLogs() {
    const allowedTypes = FILTER_MAPPINGS[this.currentFilter]
    
    if (!allowedTypes) {
      return this.logEntries
    }

    return this.logEntries.filter(log => 
      allowedTypes.includes(log.action_type) || 
      log.action_type === 'ROUND_START' ||
      log.action_type === 'ENCOUNTER_END'
    )
  }

  /**
   * Render all log entries
   */
  renderLogs() {
    const listEl = document.getElementById('combat-log-list')
    if (!listEl) return

    listEl.innerHTML = ''

    const filteredLogs = this.getFilteredLogs()
    let currentRound = null

    filteredLogs.forEach(log => {
      if (log.round_number !== currentRound && log.round_number) {
        currentRound = log.round_number
        if (log.action_type !== 'ROUND_START') {
          this.appendRoundDivider(currentRound, false)
        }
      }

      if (log.action_type === 'ROUND_START') {
        this.appendRoundDivider(log.data?.round || log.round_number, false)
      } else if (log.action_type === 'ENCOUNTER_END') {
        this.appendEncounterEnd(log.data, false)
      } else {
        this.appendLogEntry(log, false)
      }
    })

    this.scrollToBottom()
  }

  /**
   * Append a single log entry to the list
   */
  appendLogEntry(log, animate = true) {
    const listEl = document.getElementById('combat-log-list')
    if (!listEl) return

    if (!this.shouldShowLog(log)) return

    const config = ACTION_CONFIG[log.action_type] || DEFAULT_ACTION_CONFIG
    const time = this.formatTime(log.created_at)
    const message = config.format(log)

    const entryEl = document.createElement('div')
    entryEl.className = `combat-log-entry ${animate ? 'is-new' : ''}`
    entryEl.dataset.actionType = log.action_type

    entryEl.innerHTML = `
      <span class="combat-log-time">${time}</span>
      <span class="combat-log-icon">${config.icon}</span>
      <span class="combat-log-message">${this.escapeHtml(message)}</span>
    `

    listEl.appendChild(entryEl)
  }

  /**
   * Append a round divider
   */
  appendRoundDivider(roundNumber, animate = true) {
    const listEl = document.getElementById('combat-log-list')
    if (!listEl) return

    const dividerEl = document.createElement('div')
    dividerEl.className = `combat-log-divider ${animate ? 'is-new' : ''}`
    dividerEl.innerHTML = `
      <span class="combat-log-divider-line"></span>
      <span class="combat-log-divider-text">Round ${roundNumber}</span>
      <span class="combat-log-divider-line"></span>
    `

    listEl.appendChild(dividerEl)
  }

  /**
   * Append encounter end message
   */
  appendEncounterEnd(data, animate = true) {
    const listEl = document.getElementById('combat-log-list')
    if (!listEl) return

    const outcome = data?.outcome || 'Unknown'
    const endEl = document.createElement('div')
    endEl.className = `combat-log-end ${animate ? 'is-new' : ''}`
    endEl.innerHTML = `
      <div class="combat-log-end-icon">⚔️</div>
      <div class="combat-log-end-text">
        <strong>Encounter Ended</strong>
        <span>Outcome: ${this.escapeHtml(outcome)}</span>
      </div>
    `

    listEl.appendChild(endEl)
  }

  /**
   * Check if a log should be shown based on current filter
   */
  shouldShowLog(log) {
    const allowedTypes = FILTER_MAPPINGS[this.currentFilter]
    return !allowedTypes || allowedTypes.includes(log.action_type)
  }

  /**
   * Scroll the log list to the bottom
   */
  scrollToBottom() {
    const listEl = document.getElementById('combat-log-list')
    if (listEl) {
      listEl.scrollTop = listEl.scrollHeight
    }
  }

  /**
   * Format timestamp for display
   */
  formatTime(timestamp) {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit'
    })
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }

  /**
   * Fetch with authentication header
   */
  async fetchWithAuth(url, options = {}) {
    const token = getAccessToken()
    
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    })
  }

  /**
   * Show the combat log container
   */
  show() {
    const container = document.getElementById(this.containerId)
    if (container) {
      container.hidden = false
    }
  }

  /**
   * Hide the combat log container
   */
  hide() {
    const container = document.getElementById(this.containerId)
    if (container) {
      container.hidden = true
    }
  }

  /**
   * Update encounter ID and reload logs
   */
  async setEncounter(encounterId) {
    this.encounterId = encounterId
    this.logEntries = []
    
    const listEl = document.getElementById('combat-log-list')
    if (listEl) {
      listEl.innerHTML = ''
    }

    await this.loadLogHistory()
  }

  /**
   * Add a custom entry (for local messages)
   */
  addCustomEntry(message, icon = '📝') {
    const entry = {
      id: `custom-${Date.now()}`,
      action_type: 'CUSTOM',
      actor_name: 'System',
      created_at: new Date().toISOString(),
      data: { description: message, icon }
    }

    this.logEntries.push(entry)
    this.appendLogEntry(entry)
    this.scrollToBottom()
  }

  /**
   * Clean up event listeners
   */
  destroy() {
    if (this.socketClient) {
      this.socketClient.off('combat_action_logged')
      this.socketClient.off('combat_round_started')
      this.socketClient.off('encounter_ended')
    }
    this.isInitialized = false
  }
}

