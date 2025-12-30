import template from './game.html?raw'
import { Footer } from '../components/index.js'
import { navigate, getRouteParams } from '../router.js'
import { getAccessToken, getUserFromToken } from '../infrastructure/auth/auth.js'

let currentGame = null
let currentUserRole = null

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

  } catch (error) {
    loadingEl.hidden = true
    showError(error.message)
  }
}

function renderGameInfo(game) {
  const user = getUserFromToken()
  const isDM = game.dm_user_id === user?.user_id
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

  // Show leave button only for players (not DM)
  const leaveBtn = document.getElementById('leave-game-btn')
  if (!isDM && game.status === 'ACTIVE') {
    leaveBtn.hidden = false
    setupLeaveButton(game.id)
  }
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

  leaveBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to leave this game?')) {
      return
    }

    leaveBtn.disabled = true

    try {
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
    } catch (error) {
      showMessage(error.message, 'error')
      leaveBtn.disabled = false
    }
  })
}

async function loadPlayers(gameId) {
  const loadingEl = document.getElementById('players-loading')
  const listEl = document.getElementById('players-list')
  const countEl = document.getElementById('players-count')

  // For now, we show the current user as a player
  // This can be enhanced with a dedicated endpoint to get all game members
  const user = getUserFromToken()
  
  loadingEl.hidden = true
  listEl.hidden = false
  
  // Placeholder until we have a proper endpoint
  countEl.textContent = '1 member'
  listEl.innerHTML = `
    <div class="player-card">
      <div class="player-avatar">
        <span>${getInitials(user?.username || 'Unknown')}</span>
      </div>
      <div class="player-info">
        <span class="player-name">${escapeHtml(user?.username || 'Unknown')}</span>
        <span class="player-role ${currentUserRole === 'DM' ? 'role-dm' : 'role-player'}">
          ${currentUserRole === 'DM' ? 'Dungeon Master' : 'Player'}
        </span>
      </div>
      <span class="player-status-badge status-you">You</span>
    </div>
  `
}

function setupGameActions(game) {
  // Placeholder for future game actions
}

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

