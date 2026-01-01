/**
 * Game Chat Component
 * Handles real-time chat functionality for game sessions
 */

import { SocketIOClient } from '../infrastructure/realtime/socketio.js'
import { getAccessToken, getUserFromToken } from '../infrastructure/auth/auth.js'

/**
 * Creates and manages the game chat functionality
 * Works with existing HTML structure in game.html
 */
export class GameChat {
  constructor({ gameId, onMessage, onError }) {
    this.gameId = gameId
    this.onMessage = onMessage || (() => {})
    this.onError = onError || (() => {})
    this.socketClient = null
    this.currentUser = getUserFromToken()
  }

  /**
   * Initializes the chat connection and loads message history
   */
  async init() {
    this.updateConnectionStatus('connecting')
    this.setupChatForm()
    
    await this.loadMessageHistory()
    
    this.socketClient = new SocketIOClient({
      onConnected: () => {
        this.updateConnectionStatus('connected')
        this.socketClient.joinGame(parseInt(this.gameId))
      },
      onDisconnected: () => {
        this.updateConnectionStatus('disconnected')
      },
      onError: (error) => {
        this.updateConnectionStatus('disconnected')
      },
      onAuthOk: (data) => {
        // Do nothing
      }
    })

    this.registerEventHandlers()
    
    const token = getAccessToken()
    this.socketClient.connect(token)
  }

  registerEventHandlers() {
    this.socketClient.on('joined_game', this.handleJoinedGame.bind(this))
    this.socketClient.on('chat_message', this.handleChatMessage.bind(this))
    this.socketClient.on('error', this.handleSocketError.bind(this))
  }

  async loadMessageHistory() {
    const chatLoadingEl = document.getElementById('chat-loading')
    const chatEmptyEl = document.getElementById('chat-empty')

    try {
      const response = await this.fetchWithAuth(`/api/v1/game/${this.gameId}/messages?limit=50`)
      
      if (!response.ok) {
        throw new Error('Failed to load messages')
      }

      const messages = await response.json()
      
      chatLoadingEl.hidden = true
      
      if (messages.length === 0) {
        chatEmptyEl.hidden = false
      } else {
        chatEmptyEl.hidden = true
        messages.forEach(msg => this.renderMessage(msg))
        this.scrollToBottom()
      }
    } catch (error) {
      console.error('[GameChat] Failed to load history:', error)
      chatLoadingEl.hidden = true
      chatEmptyEl.hidden = false
    }
  }

  setupChatForm() {
    const form = document.getElementById('chat-form')
    const input = document.getElementById('chat-input')
    const sendBtn = document.getElementById('chat-send-btn')

    form.addEventListener('submit', (e) => {
      e.preventDefault()
      
      const content = input.value.trim()
      if (!content) return
      
      if (!this.socketClient || !this.socketClient.isConnected) {
        this.onError('Not connected to chat')
        return
      }

      this.socketClient.sendChatMessage(parseInt(this.gameId), content)
      input.value = ''
      input.focus()
    })

    input.addEventListener('input', () => {
      sendBtn.disabled = !input.value.trim()
    })
    
    sendBtn.disabled = true
  }

  handleJoinedGame(data) {
    // System message for joining is now sent from the server
  }

  handleChatMessage(message) {
    const chatEmptyEl = document.getElementById('chat-empty')
    chatEmptyEl.hidden = true
    
    this.renderMessage(message)
    this.scrollToBottom()
  }

  handleSocketError(data) {
    console.error('[GameChat] Server error:', data.code, data.message)
    this.onError(`Chat error: ${data.message}`)
  }

  renderMessage(message) {
    const chatMessagesEl = document.getElementById('chat-messages')

    // Handle system messages differently
    if (message.message_type === 'system') {
      this.addSystemMessage(message.content)
      return
    }

    const isOwn = message.user_id?.toString() === this.currentUser?.sub?.toString()
    
    const messageEl = document.createElement('div')
    messageEl.className = `chat-message ${isOwn ? 'is-own' : ''}`
    
    const time = new Date(message.created_at).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
    
    messageEl.innerHTML = `
      <div class="chat-message-avatar">
        <span>${this.getInitials(message.username || message.name || 'Unknown')}</span>
      </div>
      <div class="chat-message-content">
        <div class="chat-message-header">
          <span class="chat-message-username">${this.escapeHtml(message.username || message.name || 'Unknown')}</span>
          <span class="chat-message-time">${time}</span>
        </div>
        <div class="chat-message-text">${this.escapeHtml(message.content)}</div>
      </div>
    `
    
    chatMessagesEl.appendChild(messageEl)
  }

  addSystemMessage(text) {
    const chatMessagesEl = document.getElementById('chat-messages')
    const chatEmptyEl = document.getElementById('chat-empty')
    
    chatEmptyEl.hidden = true
    
    const messageEl = document.createElement('div')
    messageEl.className = 'chat-message chat-message-system'
    messageEl.textContent = text
    
    chatMessagesEl.appendChild(messageEl)
    this.scrollToBottom()
  }

  scrollToBottom() {
    const chatMessagesEl = document.getElementById('chat-messages')
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight
  }

  updateConnectionStatus(status) {
    const statusEl = document.getElementById('chat-connection-status')
    if (!statusEl) return
    
    const indicator = statusEl.querySelector('.status-indicator')
    const text = statusEl.querySelector('.status-text')
    
    indicator.className = 'status-indicator'
    
    switch (status) {
      case 'connected':
        indicator.classList.add('status-connected')
        text.textContent = 'Connected'
        break
      case 'connecting':
        indicator.classList.add('status-connecting')
        text.textContent = 'Connecting...'
        break
      case 'disconnected':
      default:
        indicator.classList.add('status-disconnected')
        text.textContent = 'Disconnected'
        break
    }
  }

  /**
   * Leave the chat room (notifies server before disconnecting).
   * Use this when the user navigates away from the game view.
   */
  leaveChat() {
    if (this.socketClient && this.socketClient.isConnected) {
      this.socketClient.leaveChat(parseInt(this.gameId))
    }
  }

  /**
   * Disconnects the chat and cleans up resources.
   * Should call leaveChat() first if you want to notify the server.
   */
  disconnect() {
    if (this.socketClient) {
      this.socketClient.disconnect()
      this.socketClient = null
    }
  }

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

  getInitials(name) {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }
}
