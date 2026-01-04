/**
 * Socket.IO client for real-time communication.
 * Handles connection, authentication, rooms, and events.
 * Includes combat system support with encounter tracking.
 */

import { io } from 'socket.io-client'

const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT_ATTEMPTS = 5

/**
 * Combat-related event types received from server
 */
const COMBAT_EVENTS = [
  'encounter_started',
  'initiative_updated',
  'combat_round_started',
  'turn_started',
  'combat_action_logged',
  'combatant_updated',
  'turn_timeout_warning',
  'turn_skipped',
  'player_disconnected_combat',
  'player_reconnected_combat',
  'dm_controlling_character',
  'encounter_paused',
  'encounter_ended',
  'encounter_state_sync',
]

export class SocketIOClient {
  constructor(options = {}) {
    this.socket = null
    this.isConnected = false
    this.currentGameId = null
    this.activeEncounterId = null
    this.characterId = null

    // Callbacks
    this.onConnected = options.onConnected || (() => {})
    this.onDisconnected = options.onDisconnected || (() => {})
    this.onError = options.onError || (() => {})
    this.onAuthOk = options.onAuthOk || (() => {})

    // Event handlers map
    this.eventHandlers = new Map()
  }

  /**
   * Connect to the Socket.IO server with JWT authentication.
   */
  connect(token) {
    if (this.socket?.connected) {
      console.log('[SocketIO] Already connected')
      return
    }

    const url = this._getServerUrl()
    console.log('[SocketIO] Connecting to:', url)

    this.socket = io(url, {
      auth: { token },
      transports: ['websocket'],  // Force WebSocket, skip polling
      reconnection: true,
      reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
      reconnectionDelay: RECONNECT_DELAY_MS,
    })

    this._setupEventListeners()
  }

  /**
   * Disconnect from the server.
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.isConnected = false
      this.currentGameId = null
      this.activeEncounterId = null
      this.characterId = null
    }
  }

  /**
   * Set the current character ID for combat tracking.
   */
  setCharacterId(characterId) {
    this.characterId = characterId
  }

  /**
   * Set the active encounter ID.
   */
  setActiveEncounterId(encounterId) {
    this.activeEncounterId = encounterId
  }

  /**
   * Join a game room for real-time updates.
   */
  joinGame(gameId) {
    if (!this.socket?.connected) {
      console.warn('[SocketIO] Cannot join game: not connected')
      return
    }

    this.socket.emit('join_game', { game_id: gameId })
  }

  /**
   * Leave the current game room (user abandons the game).
   */
  leaveGame(gameId) {
    if (!this.socket?.connected) {
      return
    }

    this.socket.emit('leave_game', { game_id: gameId || this.currentGameId })
    this.currentGameId = null
  }

  /**
   * Leave the chat room (user navigates away from game view).
   * User remains a member of the game, just not viewing the chat.
   */
  leaveChat(gameId) {
    if (!this.socket?.connected) {
      return
    }

    this.socket.emit('leave_chat', { game_id: gameId || this.currentGameId })
    this.currentGameId = null
  }

  /**
   * Send a chat message to the current game.
   */
  sendChatMessage(gameId, content) {
    if (!this.socket?.connected) {
      console.warn('[SocketIO] Cannot send message: not connected')
      return
    }

    this.socket.emit('chat_message', {
      game_id: gameId,
      content: content,
    })
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // COMBAT METHODS
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Roll initiative for a combatant.
   * Players roll for their character, DM can roll for NPCs.
   */
  rollInitiative(encounterId, combatantKey, roll = null, modifier = null) {
    if (!this._checkConnection('rollInitiative')) return

    this.socket.emit('roll_initiative', {
      encounter_id: encounterId,
      combatant_key: combatantKey,
      roll: roll,
      modifier: modifier,
    })
  }

  /**
   * Set initiative manually (DM only).
   */
  setInitiative(encounterId, combatantKey, value) {
    if (!this._checkConnection('setInitiative')) return

    this.socket.emit('set_initiative', {
      encounter_id: encounterId,
      combatant_key: combatantKey,
      value: value,
    })
  }

  /**
   * Submit a combat action (attack, spell, movement, etc).
   */
  submitCombatAction(encounterId, actionData) {
    if (!this._checkConnection('submitCombatAction')) return

    this.socket.emit('combat_action', {
      encounter_id: encounterId,
      action_type: actionData.actionType,
      actor_key: actionData.actorKey,
      target_key: actionData.targetKey || null,
      data: actionData.data || {},
    })
  }

  /**
   * Update a combatant's state (DM only).
   * Changes can include: hp, conditions, temp_hp, etc.
   */
  updateCombatant(encounterId, combatantKey, changes) {
    if (!this._checkConnection('updateCombatant')) return

    this.socket.emit('update_combatant', {
      encounter_id: encounterId,
      combatant_key: combatantKey,
      changes: changes,
    })
  }

  /**
   * Start an encounter (DM only).
   * Transitions encounter from READY to ACTIVE.
   */
  startEncounter(encounterId) {
    if (!this._checkConnection('startEncounter')) return

    this.socket.emit('start_encounter', {
      encounter_id: encounterId,
    })
    this.activeEncounterId = encounterId
  }

  /**
   * Advance to the next turn in combat (DM only).
   */
  nextTurn(encounterId) {
    if (!this._checkConnection('nextTurn')) return

    this.socket.emit('next_turn', {
      encounter_id: encounterId,
    })
  }

  /**
   * Pause the current encounter (DM only).
   */
  pauseEncounter(encounterId) {
    if (!this._checkConnection('pauseEncounter')) return

    this.socket.emit('pause_encounter', {
      encounter_id: encounterId,
    })
  }

  /**
   * Resume a paused encounter (DM only).
   */
  resumeEncounter(encounterId) {
    if (!this._checkConnection('resumeEncounter')) return

    this.socket.emit('resume_encounter', {
      encounter_id: encounterId,
    })
  }

  /**
   * End the current encounter (DM only).
   */
  endEncounter(encounterId, outcome) {
    if (!this._checkConnection('endEncounter')) return

    this.socket.emit('end_encounter', {
      encounter_id: encounterId,
      outcome: outcome,
    })
    this.activeEncounterId = null
  }

  /**
   * Request full encounter state sync (used after reconnection).
   */
  syncEncounterState(encounterId) {
    if (!this._checkConnection('syncEncounterState')) return

    this.socket.emit('sync_encounter_state', {
      encounter_id: encounterId,
    })
  }

  /**
   * Check if currently in an active encounter.
   */
  isInCombat() {
    return this.activeEncounterId !== null
  }

  /**
   * Get the current active encounter ID.
   */
  getActiveEncounterId() {
    return this.activeEncounterId
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EVENT REGISTRATION
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Register a handler for a specific event type.
   */
  on(eventType, handler) {
    this.eventHandlers.set(eventType, handler)

    // If socket exists, also register with socket.io
    if (this.socket) {
      this.socket.on(eventType, handler)
    }
  }

  /**
   * Remove a handler for a specific event type.
   */
  off(eventType) {
    this.eventHandlers.delete(eventType)

    if (this.socket) {
      this.socket.off(eventType)
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRIVATE METHODS
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Check if socket is connected and log warning if not.
   */
  _checkConnection(methodName) {
    if (!this.socket?.connected) {
      console.warn(`[SocketIO] Cannot ${methodName}: not connected`)
      return false
    }
    return true
  }

  _getServerUrl() {
    // Socket.IO connects to the same host by default
    // The path is /socket.io/ by default
    const protocol = window.location.protocol
    const host = window.location.host
    return `${protocol}//${host}`
  }

  _setupEventListeners() {
    // Connection events
    this.socket.on('connect', () => {
      console.log('[SocketIO] Connected')
      this.isConnected = true
      this.onConnected()
    })

    this.socket.on('disconnect', (reason) => {
      console.log('[SocketIO] Disconnected:', reason)
      this.isConnected = false
      this.currentGameId = null
      this.onDisconnected(reason)
    })

    this.socket.on('connect_error', (error) => {
      console.error('[SocketIO] Connection error:', error.message)
      this.onError(error)
    })

    // Auth response
    this.socket.on('auth_ok', (data) => {
      console.log('[SocketIO] Authenticated as:', data.username)
      this.onAuthOk(data)
    })

    // Game room events
    this.socket.on('joined_game', (data) => {
      console.log('[SocketIO] Joined game:', data.game_id)
      this.currentGameId = data.game_id
      const handler = this.eventHandlers.get('joined_game')
      if (handler) handler(data)
    })

    this.socket.on('user_joined', (data) => {
      console.log('[SocketIO] User joined:', data.username)
      const handler = this.eventHandlers.get('user_joined')
      if (handler) handler(data)
    })

    this.socket.on('user_left', (data) => {
      console.log('[SocketIO] User left:', data.username)
      const handler = this.eventHandlers.get('user_left')
      if (handler) handler(data)
    })

    // Chat events
    this.socket.on('chat_message', (data) => {
      console.log('[SocketIO] Chat message:', data)
      const handler = this.eventHandlers.get('chat_message')
      if (handler) handler(data)
    })

    // Error events
    this.socket.on('error', (data) => {
      console.error('[SocketIO] Error:', data)
      const handler = this.eventHandlers.get('error')
      if (handler) handler(data)
    })

    // Setup combat event listeners
    this._setupCombatEventListeners()

    // Re-register custom handlers
    const builtInEvents = [
      'joined_game',
      'user_joined',
      'user_left',
      'chat_message',
      'error',
      ...COMBAT_EVENTS,
    ]
    for (const [eventType, handler] of this.eventHandlers) {
      if (!builtInEvents.includes(eventType)) {
        this.socket.on(eventType, handler)
      }
    }
  }

  /**
   * Setup listeners for combat-related events.
   */
  _setupCombatEventListeners() {
    // Encounter lifecycle events
    this.socket.on('encounter_started', (data) => {
      console.log('[SocketIO] Encounter started:', data.encounter_id)
      this.activeEncounterId = data.encounter_id
      this._invokeHandler('encounter_started', data)
    })

    this.socket.on('encounter_ended', (data) => {
      console.log('[SocketIO] Encounter ended:', data.encounter_id)
      if (this.activeEncounterId === data.encounter_id) {
        this.activeEncounterId = null
      }
      this._invokeHandler('encounter_ended', data)
    })

    this.socket.on('encounter_paused', (data) => {
      console.log('[SocketIO] Encounter paused:', data.encounter_id)
      this._invokeHandler('encounter_paused', data)
    })

    this.socket.on('encounter_state_sync', (data) => {
      console.log('[SocketIO] Encounter state sync received')
      this._invokeHandler('encounter_state_sync', data)
    })

    // Initiative events
    this.socket.on('initiative_updated', (data) => {
      console.log('[SocketIO] Initiative updated for encounter:', data.encounter_id)
      this._invokeHandler('initiative_updated', data)
    })

    // Turn management events
    this.socket.on('combat_round_started', (data) => {
      console.log('[SocketIO] Combat round started:', data.round_number)
      this._invokeHandler('combat_round_started', data)
    })

    this.socket.on('turn_started', (data) => {
      console.log('[SocketIO] Turn started for:', data.current_combatant?.name)
      this._invokeHandler('turn_started', data)
    })

    this.socket.on('turn_skipped', (data) => {
      console.log('[SocketIO] Turn skipped:', data.combatant_key, 'reason:', data.reason)
      this._invokeHandler('turn_skipped', data)
    })

    this.socket.on('turn_timeout_warning', (data) => {
      console.log('[SocketIO] Turn timeout warning:', data.seconds_remaining, 'seconds remaining')
      this._invokeHandler('turn_timeout_warning', data)
    })

    // Combat action events
    this.socket.on('combat_action_logged', (data) => {
      console.log('[SocketIO] Combat action logged:', data.log_entry?.action_type)
      this._invokeHandler('combat_action_logged', data)
    })

    this.socket.on('combatant_updated', (data) => {
      console.log('[SocketIO] Combatant updated:', data.combatant_key)
      this._invokeHandler('combatant_updated', data)
    })

    // Player connection events during combat
    this.socket.on('player_disconnected_combat', (data) => {
      console.log('[SocketIO] Player disconnected during combat:', data.player_name)
      this._invokeHandler('player_disconnected_combat', data)
    })

    this.socket.on('player_reconnected_combat', (data) => {
      console.log('[SocketIO] Player reconnected during combat:', data.player_name)
      this._invokeHandler('player_reconnected_combat', data)
    })

    this.socket.on('dm_controlling_character', (data) => {
      console.log('[SocketIO] DM controlling character:', data.character_name)
      this._invokeHandler('dm_controlling_character', data)
    })
  }

  /**
   * Invoke a registered event handler if it exists.
   */
  _invokeHandler(eventType, data) {
    const handler = this.eventHandlers.get(eventType)
    if (handler) {
      handler(data)
    }
  }
}

// Singleton instance for app-wide use
let instance = null

export function getSocketIOClient(options = {}) {
  if (!instance) {
    instance = new SocketIOClient(options)
  }
  return instance
}

export function resetSocketIOClient() {
  if (instance) {
    instance.disconnect()
    instance = null
  }
}

