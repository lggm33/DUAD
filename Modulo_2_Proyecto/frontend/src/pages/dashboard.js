import template from './dashboard.html?raw'
import { Footer, showConfirmModal } from '../components/index.js'
import { navigate } from '../router.js'
import { getAccessToken, clearTokens, getUserFromToken } from '../infrastructure/auth/auth.js'

export function dashboardPage(app) {
  app.innerHTML = template + Footer()
  initDashboard()
}

async function initDashboard() {
  setupLogout()
  await loadGames()
  setupCreateGameForm()
  setupJoinGameForm()
}

function setupLogout() {
  const logoutBtn = document.getElementById('logout-btn')
  logoutBtn.addEventListener('click', async () => {
    await showConfirmModal({
      title: 'Logout',
      message: 'Are you sure you want to logout?',
      confirmText: 'Logout',
      iconType: 'leave',
      iconClass: 'modal-icon-warning',
      onConfirm: () => {
        clearTokens()
        navigate('/sign-in')
      }
    })
  })
}

async function loadGames() {
  const loadingEl = document.getElementById('games-loading')
  const emptyEl = document.getElementById('games-empty')
  const listEl = document.getElementById('games-list')
  const countEl = document.getElementById('games-count')
  const createBtn = document.getElementById('create-game-btn')
  const createForm = document.getElementById('create-game-form')
  const disabledMsg = document.getElementById('create-game-disabled-msg')

  try {
    const response = await fetchWithAuth('/api/v1/game/list-all')
    const games = await response.json()

    loadingEl.hidden = true

    if (!games || games.length === 0) {
      loadingEl.hidden = true
      emptyEl.hidden = false
      countEl.textContent = '0 games'
      return
    }

    countEl.textContent = `${games.length} game${games.length !== 1 ? 's' : ''}`
    
    const activeGames = games.filter(game => game.status === 'ACTIVE')
    const user = getUserFromToken()
    const hasActiveGameAsDM = activeGames.some(game => game.dm_user_id === user?.user_id)

    if (hasActiveGameAsDM) {
      createBtn.disabled = true
      createForm.querySelector('input').disabled = true
      disabledMsg.hidden = false
    }

    renderGamesList(games, listEl)
    setupGameActions(listEl)
    listEl.hidden = false
  } catch (error) {
    loadingEl.hidden = true
    showMessage(error.message, 'error')
  }
}

function renderGamesList(games, container) {
  const user = getUserFromToken()
  
  container.innerHTML = games.map(game => {
    const isActive = game.status === 'ACTIVE'
    const membershipStatus = game.membership_status
    const isDM = game.role_in_game === 'DM'
    const statusClass = isActive ? 'status-active' : 'status-ended'
    const roleLabel = isDM ? 'Dungeon Master' : 'Player'
    const roleClass = isDM ? 'role-dm' : 'role-player'

    return `
      <div class="game-card ${isActive ? 'game-card-active' : 'game-card-ended'}">
        <div class="game-card-header">
          <h3 class="game-card-title">${escapeHtml(game.name)}</h3>
          <span class="game-status ${statusClass}">${game.status}</span>
        </div>
        <div class="game-card-meta">
          <span class="game-role ${roleClass}">${roleLabel}</span>
          <span class="game-date">Created ${formatDate(game.created_at)}</span>
        </div>
        ${game.invite_code && membershipStatus === 'ACTIVE' ? `
          <div class="game-invite-section">
            <div class="invite-code-display">
              <span class="invite-label">Invite Code:</span>
              <code class="invite-code">${game.invite_code}</code>
            </div>
            <button class="btn btn-outline btn-sm btn-share" 
                data-action="share" 
                data-invite-code="${game.invite_code}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                <polyline points="16 6 12 2 8 6"/>
                <line x1="12" y1="2" x2="12" y2="15"/>
              </svg>
              Copy link
            </button>
          </div>
        ` : ''}
        ${isActive ? `
          <div class="game-card-actions">
            ${membershipStatus === 'KICKED' 
              ? `<span class="membership-kicked">You were kicked from this game</span>`
              : `<button class="btn ${membershipStatus === 'LEFT' ? 'btn-secondary' : 'btn-primary'} btn-sm" 
                  data-action="${membershipStatus === 'LEFT' ? 'rejoin' : 'enter'}" 
                  data-game-id="${game.id}">
                  ${membershipStatus === 'LEFT' ? 'Rejoin' : 'Enter Game'}
                </button>`
            }
          </div>
        ` : ''}
      </div>
    `
  }).join('')
}

function setupCreateGameForm() {
  const form = document.getElementById('create-game-form')
  const submitBtn = document.getElementById('create-game-btn')
  
  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    
    if (submitBtn.disabled) return

    const formData = new FormData(form)
    const gameName = formData.get('game_name')
    const user = getUserFromToken()

    setButtonLoading(submitBtn, true)
    hideMessage()

    try {
      const response = await fetchWithAuth('/api/v1/game/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: gameName,
          dm_user_id: user.sub
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to create game')
      }

      const result = await response.json()
      showMessage(`Game "${result.game.name}" created! Invite code: ${result.invite_code}`, 'success')
      form.reset()
      await loadGames()
    } catch (error) {
      showMessage(error.message, 'error')
    } finally {
      setButtonLoading(submitBtn, false)
    }
  })
}

function setupJoinGameForm() {
  const form = document.getElementById('join-game-form')
  const submitBtn = document.getElementById('join-game-btn')

  form.addEventListener('submit', async (event) => {
    event.preventDefault()

    const formData = new FormData(form)
    const inviteCode = formData.get('invite_code')

    setButtonLoading(submitBtn, true)
    hideMessage()

    try {
      const response = await fetchWithAuth('/api/v1/game/join-by-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invite_code: inviteCode })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to join game')
      }

      const result = await response.json()
      showMessage(`Successfully joined "${result.name}"!`, 'success')
      form.reset()
      await loadGames()
    } catch (error) {
      showMessage(error.message, 'error')
    } finally {
      setButtonLoading(submitBtn, false)
    }
  })
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

function setButtonLoading(button, isLoading) {
  const btnText = button.querySelector('.btn-text')
  const btnLoader = button.querySelector('.btn-loader')
  
  button.disabled = isLoading
  if (btnText) btnText.hidden = isLoading
  if (btnLoader) btnLoader.hidden = !isLoading
}

function showMessage(message, type = 'info') {
  const messageEl = document.getElementById('dashboard-message')
  messageEl.textContent = message
  messageEl.className = `dashboard-message dashboard-message-${type}`
  messageEl.hidden = false
}

function hideMessage() {
  const messageEl = document.getElementById('dashboard-message')
  messageEl.hidden = true
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

function setupGameActions(container) {
  container.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-action]')
    if (!button) return

    const action = button.dataset.action
    const gameId = button.dataset.gameId

    if (action === 'enter') {
      navigate(`/game/${gameId}`)
      return
    }

    if (action === 'share') {
      const inviteCode = button.dataset.inviteCode
      await handleShareInvite(inviteCode)
      return
    }

    if (action === 'rejoin') {
      button.disabled = true
      try {
        const user = getUserFromToken()
        const response = await fetchWithAuth('/api/v1/game/join', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game_id: parseInt(gameId), user_id: user.sub })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.message || 'Failed to rejoin game')
        }

        showMessage('Successfully rejoined the game!', 'success')
        await loadGames()
      } catch (error) {
        showMessage(error.message, 'error')
        button.disabled = false
      }
    }
  })
}

async function handleShareInvite(inviteCode) {
  const joinUrl = `${window.location.origin}/join/${inviteCode}`

  try {
    await navigator.clipboard.writeText(joinUrl)
    showMessage('Invite link copied to clipboard!', 'success')
  } catch (err) {
    showMessage(`Share this link: ${joinUrl}`, 'info')
  }
}
