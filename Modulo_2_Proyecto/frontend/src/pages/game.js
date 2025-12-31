import template from './game.html?raw'
import { Footer, showConfirmModal } from '../components/index.js'
import { navigate, getRouteParams } from '../router.js'
import { getAccessToken, getUserFromToken } from '../infrastructure/auth/auth.js'
import { SocketIOClient } from '../infrastructure/realtime/socketio.js'

let currentGame = null
let currentUserRole = null
let socketClient = null
let currentUser = null

export function gamePage(app) {
  app.innerHTML = template + Footer()
  initGame()
}

async function initGame() {
  const { id: gameId } = getRouteParams()
  
  if (!gameId) {
    showError('Invalid game ID')
    return
  }

  currentUser = getUserFromToken()
  await loadGame(gameId)
}

async function loadGame(gameId) {
  const loadingEl = document.getElementById('game-loading')
  const errorEl = document.getElementById('game-error')
  const contentEl = document.getElementById('game-content')

  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}`)
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to load game')
    }

    const game = await response.json()
    currentGame = game

    loadingEl.hidden = true
    contentEl.hidden = false

    renderGameInfo(game)
    setupGameActions(game)
    await loadPlayers(gameId)
    
    // Initialize chat
    await initChat(gameId)

  } catch (error) {
    loadingEl.hidden = true
    showError(error.message)
  }
}

function renderGameInfo(game) {
  const user = getUserFromToken()
  const isDM = game.dm_user_id.toString() === user?.sub.toString()
  currentUserRole = isDM ? 'DM' : 'PLAYER'

  document.getElementById('game-name').textContent = game.name
  
  const statusBadge = document.getElementById('game-status')
  statusBadge.textContent = game.status
  statusBadge.className = `game-status-badge ${game.status === 'ACTIVE' ? 'status-active' : 'status-ended'}`
  
  const roleBadge = document.getElementById('game-role')
  roleBadge.textContent = isDM ? 'Dungeon Master' : 'Player'
  roleBadge.className = `game-role-badge ${isDM ? 'role-dm' : 'role-player'}`

  // Show DM section only for Dungeon Master
  const dmSection = document.getElementById('dm-section')
  if (isDM) {
    dmSection.hidden = false
    loadInviteCode(game.id)
    setupCopyInviteButton()
  }

  // Show leave button and set it up
  const leaveBtn = document.getElementById('leave-game-btn')
  leaveBtn.hidden = false
  setupLeaveButton(game.id)
}

async function loadInviteCode(gameId) {
  const inviteCodeEl = document.getElementById('invite-code')
  
  try {
    // For now, we'll show a placeholder since we need an endpoint to get the invite code
    // This could be enhanced later with a dedicated endpoint
    inviteCodeEl.textContent = 'Ask your DM for the invite code'
  } catch (error) {
    inviteCodeEl.textContent = 'Unable to load'
  }
}

function setupCopyInviteButton() {
  const copyBtn = document.getElementById('copy-invite-btn')
  const inviteCodeEl = document.getElementById('invite-code')

  copyBtn.addEventListener('click', async () => {
    const code = inviteCodeEl.textContent
    if (code && code !== 'Loading...' && code !== 'Unable to load') {
      try {
        await navigator.clipboard.writeText(code)
        showMessage('Invite code copied!', 'success')
      } catch {
        showMessage('Failed to copy', 'error')
      }
    }
  })
}

function setupLeaveButton(gameId) {
  const leaveBtn = document.getElementById('leave-game-btn')
  const user = getUserFromToken()

  leaveBtn.addEventListener('click', () => {
    showLeaveModal(gameId, user)
  })
}

async function showLeaveModal(gameId, user) {
  const isDM = currentUserRole === 'DM'

  const title = isDM ? 'End Game Session' : 'Leave Game'
  const message = isDM
    ? `As the <strong>Dungeon Master</strong>, leaving this game will <strong>end the session for all players</strong>. 
       This action cannot be undone.<br><br>
       Are you sure you want to end this game?`
    : 'Are you sure you want to leave this game? You can rejoin later if the game is still active.'
  const confirmText = isDM ? 'End Game' : 'Leave Game'
  const iconClass = isDM ? 'modal-icon-dm' : 'modal-icon-warning'

  try {
    await showConfirmModal({
      title,
      message,
      confirmText,
      iconType: 'leave',
      iconClass,
      onConfirm: async () => {
        // Disconnect WebSocket before leaving
        disconnectChat()
        
        const response = await fetchWithAuth('/api/v1/game/leave', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            game_id: parseInt(gameId), 
            user_id: user.sub 
          })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.message || 'Failed to leave game')
        }

        navigate('/dashboard')
      }
    })
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

async function loadPlayers(gameId) {
  const loadingEl = document.getElementById('players-loading')
  const listEl = document.getElementById('players-list')
  const countEl = document.getElementById('players-count')

  // For now, we show the current user as a player
  // This can be enhanced with a dedicated endpoint to get all game members
  const user = getUserFromToken()
  const membersResponse = await fetchWithAuth(`/api/v1/game/${gameId}/members`)
  if (!membersResponse.ok) {
    throw new Error('Failed to load current user')
  }
  const members = await membersResponse.json()
  
  loadingEl.hidden = true
  listEl.hidden = false
  
  // Placeholder until we have a proper endpoint
  countEl.textContent = `${members.length} member${members.length !== 1 ? 's' : ''}`
  const canKick = currentUserRole === 'DM'
  
  listEl.innerHTML = members.map(member => {
    const isDM = member.role_in_game === 'DM'
    const isCurrentUser = member.user_id.toString() === user?.sub.toString()
    const membershipStatus = member.status
    const isActive = membershipStatus === 'ACTIVE'
    const showKickButton = canKick && !isCurrentUser && !isDM && isActive
    
    return `
      <div class="player-card ${!isActive ? 'player-card-inactive' : ''}">
        <div class="player-avatar">
          <span>${getInitials(member?.username || member?.name || 'Unknown')}</span>
        </div>
        <div class="player-info">
          <span class="player-name">${escapeHtml(member?.username || member?.name || 'Unknown')}</span>
          <div class="player-badges">
            <span class="player-role ${isDM ? 'role-dm' : 'role-player'}">
              ${isDM ? 'Dungeon Master' : 'Player'}
            </span>
            ${!isActive ? `<span class="player-membership-status status-${membershipStatus.toLowerCase()}">${membershipStatus}</span>` : ''}
          </div>
        </div>
        ${isCurrentUser ? '<span class="player-status-badge status-you">You</span>' : ''}
        ${showKickButton ? `
          <button class="btn btn-ghost btn-kick" data-user-id="${member.user_id}" title="Kick player">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        ` : ''}
      </div>
    `
  }).join('')

  setupKickButtons(gameId)
}

function setupKickButtons(gameId) {
  const kickButtons = document.querySelectorAll('.btn-kick')
  
  kickButtons.forEach(button => {
    button.addEventListener('click', async (event) => {
      event.stopPropagation()
      const userId = button.dataset.userId
      await handleKickUser(gameId, userId)
    })
  })
}

async function handleKickUser(gameId, userId) {
  try {
    const confirmed = await showConfirmModal({
      title: 'Kick Player',
      message: 'Are you sure you want to kick this player from the game? They can rejoin if they have the invite code.',
      confirmText: 'Kick Player',
      iconType: 'danger',
      iconClass: 'modal-icon-warning',
      onConfirm: async () => {
        const response = await fetchWithAuth('/api/v1/game/kick', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            game_id: parseInt(gameId), 
            user_id: parseInt(userId) 
          })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.message || 'Failed to kick player')
        }
      }
    })

    if (confirmed) {
      showMessage('Player kicked successfully', 'success')
      await loadPlayers(gameId)
    }
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

function setupGameActions(game) {
  // Setup chat form
  setupChatForm()
  
  // Cleanup on page navigation
  window.addEventListener('beforeunload', disconnectChat)
}

// ========================================
// Chat Functions
// ========================================

async function initChat(gameId) {
  updateConnectionStatus('connecting')
  
  // Load message history first
  await loadMessageHistory(gameId)
  
  // Initialize Socket.IO connection
  socketClient = new SocketIOClient({
    onConnected: () => {
      updateConnectionStatus('connected')
      // Join the game room after connection
      socketClient.joinGame(parseInt(gameId))
    },
    onDisconnected: () => {
      updateConnectionStatus('disconnected')
    },
    onError: (error) => {
      console.error('[Chat] Socket.IO error:', error)
      updateConnectionStatus('disconnected')
    },
    onAuthOk: (data) => {
      console.log('[Chat] Authenticated as:', data.username)
    }
  })

  // Register event handlers
  socketClient.on('joined_game', handleJoinedGame)
  socketClient.on('chat_message', handleChatMessageCreated)
  socketClient.on('user_joined', handleUserJoined)
  socketClient.on('user_left', handleUserLeft)
  socketClient.on('error', handleWsError)

  // Connect with JWT token
  const token = getAccessToken()
  socketClient.connect(token)
}

async function loadMessageHistory(gameId) {
  const chatLoadingEl = document.getElementById('chat-loading')
  const chatEmptyEl = document.getElementById('chat-empty')
  const chatMessagesEl = document.getElementById('chat-messages')

  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/messages?limit=50`)
    
    if (!response.ok) {
      throw new Error('Failed to load messages')
    }

    const messages = await response.json()
    
    chatLoadingEl.hidden = true
    
    if (messages.length === 0) {
      chatEmptyEl.hidden = false
    } else {
      chatEmptyEl.hidden = true
      messages.forEach(msg => renderChatMessage(msg))
      scrollToBottom()
    }
  } catch (error) {
    console.error('[Chat] Failed to load history:', error)
    chatLoadingEl.hidden = true
    chatEmptyEl.hidden = false
  }
}

function setupChatForm() {
  const form = document.getElementById('chat-form')
  const input = document.getElementById('chat-input')
  const sendBtn = document.getElementById('chat-send-btn')

  form.addEventListener('submit', (e) => {
    e.preventDefault()
    
    const content = input.value.trim()
    if (!content) return
    
    if (!socketClient || !socketClient.isConnected) {
      showMessage('Not connected to chat', 'error')
      return
    }

    socketClient.sendChatMessage(parseInt(currentGame.id), content)
    input.value = ''
    input.focus()
  })

  // Enable/disable send button based on input
  input.addEventListener('input', () => {
    sendBtn.disabled = !input.value.trim()
  })
  
  sendBtn.disabled = true
}

function handleJoinedGame(data) {
  console.log('[Chat] Joined game:', data.game_id)
  addSystemMessage(`You joined the adventure`)
}

function handleChatMessageCreated(message) {
  // Socket.IO sends the message directly, not wrapped in {message: ...}
  
  // Hide empty state if visible
  const chatEmptyEl = document.getElementById('chat-empty')
  chatEmptyEl.hidden = true
  
  renderChatMessage(message)
  scrollToBottom()
}

function handleUserJoined(data) {
  addSystemMessage(`${data.username} joined the adventure`)
}

function handleUserLeft(data) {
  addSystemMessage(`${data.username} left the adventure`)
}

function handleWsError(data) {
  console.error('[Chat] Server error:', data.code, data.message)
  showMessage(`Chat error: ${data.message}`, 'error')
}

function renderChatMessage(message) {
  const chatMessagesEl = document.getElementById('chat-messages')
  const isOwn = message.user_id.toString() === currentUser?.sub.toString()
  
  const messageEl = document.createElement('div')
  messageEl.className = `chat-message ${isOwn ? 'is-own' : ''}`
  
  const time = new Date(message.created_at).toLocaleTimeString([], { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
  
  messageEl.innerHTML = `
    <div class="chat-message-avatar">
      <span>${getInitials(message.username || 'Unknown')}</span>
    </div>
    <div class="chat-message-content">
      <div class="chat-message-header">
        <span class="chat-message-username">${escapeHtml(message.username || 'Unknown')}</span>
        <span class="chat-message-time">${time}</span>
      </div>
      <div class="chat-message-text">${escapeHtml(message.content)}</div>
    </div>
  `
  
  chatMessagesEl.appendChild(messageEl)
}

function addSystemMessage(text) {
  const chatMessagesEl = document.getElementById('chat-messages')
  
  // Hide empty state if visible
  const chatEmptyEl = document.getElementById('chat-empty')
  chatEmptyEl.hidden = true
  
  const messageEl = document.createElement('div')
  messageEl.className = 'chat-message chat-message-system'
  messageEl.textContent = text
  
  chatMessagesEl.appendChild(messageEl)
  scrollToBottom()
}

function scrollToBottom() {
  const chatMessagesEl = document.getElementById('chat-messages')
  chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight
}

function updateConnectionStatus(status) {
  const statusEl = document.getElementById('chat-connection-status')
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

function disconnectChat() {
  if (socketClient) {
    socketClient.disconnect()
    socketClient = null
  }
}

// ========================================
// Utility Functions
// ========================================

function showError(message) {
  const loadingEl = document.getElementById('game-loading')
  const errorEl = document.getElementById('game-error')
  const errorMsgEl = document.getElementById('game-error-message')
  
  loadingEl.hidden = true
  errorEl.hidden = false
  errorMsgEl.textContent = message
}

function showMessage(message, type = 'info') {
  const messageEl = document.getElementById('game-message')
  messageEl.textContent = message
  messageEl.className = `game-message game-message-${type}`
  messageEl.hidden = false

  setTimeout(() => {
    messageEl.hidden = true
  }, 3000)
}

async function fetchWithAuth(url, options = {}) {
  const token = getAccessToken()
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  })
}

function getInitials(name) {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
