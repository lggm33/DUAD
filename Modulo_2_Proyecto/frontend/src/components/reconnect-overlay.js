/**
 * ReconnectOverlay Component
 *
 * Fullscreen overlay that appears when WebSocket connection is lost during combat.
 * Shows reconnection status, attempt counter, and provides manual retry options.
 */

const CONTAINER_ID = 'reconnect-overlay'
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY_MS = 3000

const STATUS = {
  HIDDEN: 'hidden',
  ATTEMPTING: 'attempting',
  CONNECTED: 'connected',
  FAILED: 'failed',
}

export class ReconnectOverlay {
  /**
   * @param {Object} options - Configuration options
   * @param {Object} options.socketClient - SocketIO client instance
   * @param {Function} options.onReconnected - Callback when reconnection succeeds
   * @param {Function} options.onReturnToDashboard - Callback to navigate to dashboard
   * @param {number|null} options.activeEncounterId - Current active encounter ID (if any)
   */
  constructor(options = {}) {
    this.socketClient = options.socketClient
    this.onReconnected = options.onReconnected
    this.onReturnToDashboard = options.onReturnToDashboard
    this.activeEncounterId = options.activeEncounterId || null

    this.status = STATUS.HIDDEN
    this.reconnectAttempts = 0
    this.maxAttempts = MAX_RECONNECT_ATTEMPTS
    this.reconnectTimeout = null
    this.autoHideTimeout = null

    this.boundHandleDisconnect = this.handleDisconnect.bind(this)
    this.boundHandleReconnect = this.handleReconnect.bind(this)
    this.boundHandleReconnectAttempt = this.handleReconnectAttempt.bind(this)
    this.boundHandleReconnectFailed = this.handleReconnectFailed.bind(this)
  }

  /**
   * Initialize the overlay and register socket handlers
   */
  init() {
    this.ensureContainerExists()
    this.registerSocketHandlers()
  }

  /**
   * Cleanup resources
   */
  destroy() {
    this.unregisterSocketHandlers()
    this.clearTimeouts()
    this.removeContainer()
  }

  /**
   * Set the active encounter ID for sync requests
   */
  setActiveEncounterId(encounterId) {
    this.activeEncounterId = encounterId
  }

  /**
   * Register WebSocket event handlers
   */
  registerSocketHandlers() {
    if (!this.socketClient) return

    const socket = this.socketClient.socket
    if (!socket) return

    socket.io.on('reconnect_attempt', this.boundHandleReconnectAttempt)
    socket.io.on('reconnect', this.boundHandleReconnect)
    socket.io.on('reconnect_failed', this.boundHandleReconnectFailed)
    socket.on('disconnect', this.boundHandleDisconnect)
    socket.on('connect', this.boundHandleReconnect)
  }

  /**
   * Unregister WebSocket event handlers
   */
  unregisterSocketHandlers() {
    if (!this.socketClient?.socket) return

    const socket = this.socketClient.socket

    socket.io.off('reconnect_attempt', this.boundHandleReconnectAttempt)
    socket.io.off('reconnect', this.boundHandleReconnect)
    socket.io.off('reconnect_failed', this.boundHandleReconnectFailed)
    socket.off('disconnect', this.boundHandleDisconnect)
    socket.off('connect', this.boundHandleReconnect)
  }

  /**
   * Clear all timeouts
   */
  clearTimeouts() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    if (this.autoHideTimeout) {
      clearTimeout(this.autoHideTimeout)
      this.autoHideTimeout = null
    }
  }

  /**
   * Ensure the container exists in the DOM
   */
  ensureContainerExists() {
    let container = document.getElementById(CONTAINER_ID)
    if (!container) {
      container = document.createElement('div')
      container.id = CONTAINER_ID
      container.className = 'reconnect-overlay'
      container.hidden = true
      document.body.appendChild(container)
    }
    return container
  }

  /**
   * Remove container from DOM
   */
  removeContainer() {
    const container = document.getElementById(CONTAINER_ID)
    if (container) {
      container.remove()
    }
  }

  /**
   * Handle socket disconnect event
   */
  handleDisconnect(reason) {
    console.log('[ReconnectOverlay] Disconnected:', reason)

    if (reason === 'io client disconnect') {
      return
    }

    this.reconnectAttempts = 0
    this.show('attempting')
  }

  /**
   * Handle reconnect attempt event
   */
  handleReconnectAttempt(attemptNumber) {
    console.log('[ReconnectOverlay] Reconnect attempt:', attemptNumber)
    this.reconnectAttempts = attemptNumber
    this.updateStatus('attempting')
  }

  /**
   * Handle successful reconnection
   */
  handleReconnect() {
    console.log('[ReconnectOverlay] Reconnected!')
    this.updateStatus('connected')

    this.requestStateSync()

    this.autoHideTimeout = setTimeout(() => {
      this.hide()

      if (this.onReconnected) {
        this.onReconnected()
      }
    }, 2000)
  }

  /**
   * Handle reconnection failure
   */
  handleReconnectFailed() {
    console.log('[ReconnectOverlay] Reconnection failed')
    this.updateStatus('failed')
  }

  /**
   * Request state sync from server after reconnection
   */
  requestStateSync() {
    if (!this.socketClient?.socket?.connected) return

    if (this.activeEncounterId) {
      this.socketClient.socket.emit('sync_encounter_state', {
        encounter_id: this.activeEncounterId,
      })
    }

    if (this.socketClient.currentGameId) {
      this.socketClient.joinGame(this.socketClient.currentGameId)
    }
  }

  /**
   * Show the overlay with a reason
   */
  show(reason = 'attempting') {
    this.status = reason
    this.render()

    const container = document.getElementById(CONTAINER_ID)
    if (container) {
      container.hidden = false
      container.classList.add('ro-visible')
    }
  }

  /**
   * Update the overlay status
   */
  updateStatus(status) {
    this.status = status
    this.render()
  }

  /**
   * Hide the overlay
   */
  hide() {
    this.clearTimeouts()

    const container = document.getElementById(CONTAINER_ID)
    if (container) {
      container.classList.remove('ro-visible')
      container.classList.add('ro-hiding')

      setTimeout(() => {
        container.hidden = true
        container.classList.remove('ro-hiding')
        this.status = STATUS.HIDDEN
      }, 300)
    }
  }

  /**
   * Manual retry connection
   */
  retryConnection() {
    this.reconnectAttempts = 0
    this.updateStatus('attempting')

    if (this.socketClient?.socket) {
      this.socketClient.socket.connect()
    }
  }

  /**
   * Return to dashboard
   */
  returnToDashboard() {
    this.hide()

    if (this.onReturnToDashboard) {
      this.onReturnToDashboard()
    } else {
      window.location.href = '/dashboard'
    }
  }

  /**
   * Render the overlay content
   */
  render() {
    const container = document.getElementById(CONTAINER_ID)
    if (!container) return

    container.innerHTML = this.getContentForStatus()
    this.setupEventListeners()
  }

  /**
   * Get HTML content based on current status
   */
  getContentForStatus() {
    switch (this.status) {
      case 'attempting':
        return this.renderAttemptingContent()
      case 'connected':
        return this.renderConnectedContent()
      case 'failed':
        return this.renderFailedContent()
      default:
        return ''
    }
  }

  /**
   * Render attempting to reconnect content
   */
  renderAttemptingContent() {
    const attemptText =
      this.reconnectAttempts > 0
        ? `Attempt ${this.reconnectAttempts} of ${this.maxAttempts}`
        : 'Initializing...'

    return `
      <div class="ro-content">
        <div class="ro-spinner">
          <div class="ro-spinner-ring"></div>
          <div class="ro-spinner-ring"></div>
          <div class="ro-spinner-ring"></div>
        </div>
        
        <h2 class="ro-title">Connection Lost</h2>
        <p class="ro-message">Attempting to reconnect...</p>
        
        <div class="ro-attempts">
          <span class="ro-attempts-text">${attemptText}</span>
          <div class="ro-attempts-bar">
            <div 
              class="ro-attempts-progress" 
              style="width: ${(this.reconnectAttempts / this.maxAttempts) * 100}%"
            ></div>
          </div>
        </div>
        
        <div class="ro-note">
          <svg class="ro-note-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>Don't worry - your turn will be preserved</span>
        </div>
      </div>
    `
  }

  /**
   * Render connected content
   */
  renderConnectedContent() {
    return `
      <div class="ro-content ro-content-success">
        <div class="ro-success-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        </div>
        
        <h2 class="ro-title ro-title-success">Reconnected!</h2>
        <p class="ro-message">Syncing combat state...</p>
        
        <div class="ro-sync-indicator">
          <div class="ro-sync-dot"></div>
          <div class="ro-sync-dot"></div>
          <div class="ro-sync-dot"></div>
        </div>
      </div>
    `
  }

  /**
   * Render failed content
   */
  renderFailedContent() {
    return `
      <div class="ro-content ro-content-failed">
        <div class="ro-failed-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        </div>
        
        <h2 class="ro-title ro-title-failed">Connection Failed</h2>
        <p class="ro-message">Unable to reconnect to the server after ${this.maxAttempts} attempts.</p>
        
        <div class="ro-actions">
          <button class="btn ro-btn-retry" id="ro-retry-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            Try Again
          </button>
          <button class="btn ro-btn-dashboard" id="ro-dashboard-btn">
            Return to Dashboard
          </button>
        </div>
        
        <p class="ro-hint">
          If the problem persists, check your internet connection or try refreshing the page.
        </p>
      </div>
    `
  }

  /**
   * Setup event listeners after render
   */
  setupEventListeners() {
    const retryBtn = document.getElementById('ro-retry-btn')
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.retryConnection())
    }

    const dashboardBtn = document.getElementById('ro-dashboard-btn')
    if (dashboardBtn) {
      dashboardBtn.addEventListener('click', () => this.returnToDashboard())
    }
  }
}

