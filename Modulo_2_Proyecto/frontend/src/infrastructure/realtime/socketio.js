/**
 * Socket.IO client for real-time communication.
 * Handles connection, authentication, rooms, and events.
 */

import { io } from 'socket.io-client'

const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT_ATTEMPTS = 5

export class SocketIOClient {
  constructor(options = {}) {
    this.socket = null
    this.isConnected = false
    this.currentGameId = null

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
    }
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
   * Leave the current game room.
   */
  leaveGame(gameId) {
    if (!this.socket?.connected) {
      return
    }

    this.socket.emit('leave_game', { game_id: gameId || this.currentGameId })
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

  // Private methods

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

    // Re-register custom handlers
    for (const [eventType, handler] of this.eventHandlers) {
      if (!['joined_game', 'user_joined', 'user_left', 'chat_message', 'error'].includes(eventType)) {
        this.socket.on(eventType, handler)
      }
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

