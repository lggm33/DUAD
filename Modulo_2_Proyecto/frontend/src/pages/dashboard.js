import template from './dashboard.html?raw'
import { Footer, showConfirmModal, GameCreator } from '../components/index.js'
import { navigate } from '../router.js'
import { clearTokens, getUserFromToken } from '../infrastructure/auth/auth.js'
import { fetchWithAuth, escapeHtml, formatDate } from '../utils/index.js'

let gameCreator = null
let allGames = []
let currentFilter = 'all'

export function dashboardPage(app) {
  app.innerHTML = template + Footer()
  initDashboard()
}

async function initDashboard() {
  const user = getUserFromToken()
  const adminLink = document.getElementById('admin-link')
  if (adminLink && user && user.role === 'ADMIN') {
    adminLink.hidden = false
  }

  setupLogout()
  setupProfileButton()
  setupTabs()
  await loadGames()
  setupCreateGameButton()
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

function setupProfileButton() {
  const profileBtn = document.getElementById('profile-btn')
  if (profileBtn) {
    profileBtn.addEventListener('click', () => {
      navigate('/profile')
    })
  }
}

async function loadGames() {
  const loadingEl = document.getElementById('games-loading')
  const emptyEl = document.getElementById('games-empty')
  const listEl = document.getElementById('games-list')
  const countEl = document.getElementById('games-count')
  const createBtn = document.getElementById('open-game-creator-btn')
  const disabledMsg = document.getElementById('create-game-disabled-msg')

  try {
    const response = await fetchWithAuth('/api/v1/game/list-all')
    const games = await response.json()

    loadingEl.hidden = true
    allGames = games || []

    updateTabCounts()

    if (!games || games.length === 0) {
      emptyEl.hidden = false
      countEl.textContent = '0 games'
      return
    }

    countEl.textContent = `${games.length} game${games.length !== 1 ? 's' : ''}`
    
    const activeGames = games.filter(game => game.status === 'ACTIVE')
    const user = getUserFromToken()
    const hasActiveGameAsDM = activeGames.some(game => game.dm_user_id === user?.user_id)

    if (hasActiveGameAsDM && createBtn) {
      createBtn.disabled = true
      disabledMsg.hidden = false
    } else if (createBtn) {
      createBtn.disabled = false
      disabledMsg.hidden = true
    }

    renderFilteredGames()
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
    const canLeave = isActive && membershipStatus === 'ACTIVE'

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
            ${canLeave ? `
              <button class="btn btn-leave btn-sm" 
                  data-action="leave" 
                  data-game-id="${game.id}"
                  data-game-name="${escapeHtml(game.name)}"
                  data-is-dm="${isDM}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16 17 21 12 16 7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                ${isDM ? 'End Game' : 'Leave'}
              </button>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `
  }).join('')
}

function setupTabs() {
  const tabsContainer = document.querySelector('.games-tabs')
  if (!tabsContainer) return

  tabsContainer.addEventListener('click', (event) => {
    const tab = event.target.closest('.games-tab')
    if (!tab) return

    const tabs = tabsContainer.querySelectorAll('.games-tab')
    tabs.forEach(t => t.classList.remove('active'))
    tab.classList.add('active')

    currentFilter = tab.dataset.filter
    renderFilteredGames()
  })
}

function updateTabCounts() {
  const activeCount = allGames.filter(g => g.status === 'ACTIVE').length
  const endedCount = allGames.filter(g => g.status === 'ENDED').length
  
  const countAll = document.getElementById('tab-count-all')
  const countActive = document.getElementById('tab-count-active')
  const countEnded = document.getElementById('tab-count-ended')
  
  if (countAll) countAll.textContent = allGames.length
  if (countActive) countActive.textContent = activeCount
  if (countEnded) countEnded.textContent = endedCount
}

function getFilteredGames() {
  if (currentFilter === 'active') {
    return allGames.filter(g => g.status === 'ACTIVE')
  }
  if (currentFilter === 'ended') {
    return allGames.filter(g => g.status === 'ENDED')
  }
  return allGames
}

function renderFilteredGames() {
  const listEl = document.getElementById('games-list')
  const emptyEl = document.getElementById('games-empty')
  
  const filteredGames = getFilteredGames()
  
  if (filteredGames.length === 0) {
    listEl.hidden = true
    emptyEl.hidden = false
    return
  }
  
  emptyEl.hidden = true
  renderGamesList(filteredGames, listEl)
  setupGameActions(listEl)
  listEl.hidden = false
}

function setupCreateGameButton() {
  const createBtn = document.getElementById('open-game-creator-btn')
  
  if (!createBtn) return

  createBtn.addEventListener('click', () => {
    if (createBtn.disabled) return
    openGameCreator()
  })
}

function openGameCreator() {
  if (gameCreator) {
    gameCreator.destroy()
  }

  gameCreator = new GameCreator({
    onSuccess: async (result) => {
      const gameName = result.game?.name || result.name || 'Game'
      const inviteCode = result.invite_code || ''
      
      showMessage(
        `Game "${gameName}" created!${inviteCode ? ` Invite code: ${inviteCode}` : ''}`, 
        'success'
      )
      
      gameCreator = null
      await loadGames()
    },
    onCancel: () => {
      gameCreator = null
    }
  })

  gameCreator.init()
}

function setupJoinGameForm() {
  const form = document.getElementById('join-game-form')

  form.addEventListener('submit', (event) => {
    event.preventDefault()

    const formData = new FormData(form)
    const inviteCode = formData.get('invite_code')?.trim()

    if (!inviteCode) {
      showMessage('Please enter an invite code', 'error')
      return
    }

    navigate(`/join/${inviteCode}`)
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

    if (action === 'leave') {
      const gameName = button.dataset.gameName
      const isDM = button.dataset.isDm === 'true'
      await handleLeaveGame(gameId, gameName, isDM, button)
    }
  })
}

async function handleLeaveGame(gameId, gameName, isDM, button) {
  const title = isDM ? 'End Game Session' : 'Leave Game'
  const message = isDM
    ? `As the <strong>Dungeon Master</strong>, leaving "${gameName}" will <strong>end the session for all players</strong>. This action cannot be undone.`
    : `Are you sure you want to leave "${gameName}"? You can rejoin later using the invite code.`
  const confirmText = isDM ? 'End Game' : 'Leave Game'
  const iconClass = isDM ? 'modal-icon-dm' : 'modal-icon-warning'

  await showConfirmModal({
    title,
    message,
    confirmText,
    iconType: 'leave',
    iconClass,
    onConfirm: async () => {
      button.disabled = true
      try {
        const user = getUserFromToken()
        const response = await fetchWithAuth('/api/v1/game/leave', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game_id: parseInt(gameId), user_id: user.sub })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.message || 'Failed to leave game')
        }

        const successMsg = isDM 
          ? `Game "${gameName}" has been ended` 
          : `You have left "${gameName}"`
        showMessage(successMsg, 'success')
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
