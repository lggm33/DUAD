import template from './admin-dashboard.html?raw'
import './admin-dashboard.css'
import { getUserFromToken } from '../infrastructure/auth/auth.js'
import { fetchWithAuth, escapeHtml, formatDate } from '../utils/index.js'
import { navigate } from '../router.js'
import { showConfirmModal } from '../components/index.js'

let allGames = []
let allUsers = []
let currentFilters = {
  status: '',
  user_id: '',
  search: ''
}
let searchTimeout = null

export function adminDashboardPage(app) {
  const user = getUserFromToken()
  if (!user || user.role !== 'ADMIN') {
    navigate('/dashboard')
    return
  }
  
  app.innerHTML = template
  initAdminDashboard()
}

async function initAdminDashboard() {
  setupNavigation()
  setupFilters()
  setupModal()
  
  try {
    await Promise.all([
      loadUsers(),
      loadGames()
    ])
  } catch (error) {
    console.error('Error initializing admin dashboard:', error)
    showMessage('Failed to load dashboard data', 'error')
  }
}

function setupNavigation() {
  const backBtn = document.getElementById('back-to-dashboard')
  if (backBtn) {
    backBtn.addEventListener('click', () => navigate('/dashboard'))
  }
}

async function loadUsers() {
  try {
    const response = await fetchWithAuth('/api/v1/admin/users')
    if (!response.ok) throw new Error('Failed to load users')
    
    const data = await response.json()
    allUsers = data.users || []
    
    const userSelect = document.getElementById('filter-user')
    if (userSelect) {
      allUsers.forEach(user => {
        const option = document.createElement('option')
        option.value = user.id
        option.textContent = `${user.name} (@${user.username || user.id})`
        userSelect.appendChild(option)
      })
    }
  } catch (error) {
    console.error('Error loading users:', error)
  }
}

async function loadGames() {
  const loadingEl = document.getElementById('games-loading')
  const emptyEl = document.getElementById('games-empty')
  const tableWrapper = document.getElementById('games-table-wrapper')
  const countEl = document.getElementById('games-count')
  
  loadingEl.hidden = false
  tableWrapper.hidden = true
  emptyEl.hidden = true
  
  try {
    const params = new URLSearchParams()
    if (currentFilters.status) params.append('status', currentFilters.status)
    if (currentFilters.user_id) params.append('user_id', currentFilters.user_id)
    if (currentFilters.search) params.append('search', currentFilters.search)
    
    const response = await fetchWithAuth(`/api/v1/admin/games?${params.toString()}`)
    if (!response.ok) throw new Error('Failed to load games')
    
    const data = await response.json()
    allGames = data.games || []
    
    loadingEl.hidden = true
    countEl.textContent = `${allGames.length} game${allGames.length !== 1 ? 's' : ''} found`
    
    if (allGames.length === 0) {
      emptyEl.hidden = false
    } else {
      renderGamesTable()
      tableWrapper.hidden = false
    }
  } catch (error) {
    loadingEl.hidden = true
    showMessage(error.message, 'error')
  }
}

function renderGamesTable() {
  const tbody = document.getElementById('games-tbody')
  tbody.innerHTML = allGames.map(game => {
    const statusClass = game.status === 'ACTIVE' ? 'status-active' : 'status-ended'
    const canEnd = game.status === 'ACTIVE'
    
    return `
      <tr>
        <td><span class="text-muted">#${game.id}</span></td>
        <td><strong>${escapeHtml(game.name)}</strong></td>
        <td>
          <div class="dm-info">
            <span>${escapeHtml(game.dm_user.name)}</span>
            <small class="text-muted">@${escapeHtml(game.dm_user.username || game.dm_user.id)}</small>
          </div>
        </td>
        <td>
          <span class="players-count">${game.players_count} players</span>
        </td>
        <td>
          <span class="status-badge ${statusClass}">${game.status}</span>
        </td>
        <td>
          <span class="text-muted">${formatDate(game.created_at)}</span>
        </td>
        <td class="text-right">
          <div class="action-buttons">
            <button class="btn btn-outline btn-sm" data-action="view-players" data-game-id="${game.id}" data-game-name="${escapeHtml(game.name)}">
              Members
            </button>
            ${canEnd ? `
              <button class="btn btn-sm-danger" data-action="end-game" data-game-id="${game.id}" data-game-name="${escapeHtml(game.name)}">
                End Game
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `
  }).join('')
  
  setupTableActions()
}

function setupFilters() {
  const statusSelect = document.getElementById('filter-status')
  const userSelect = document.getElementById('filter-user')
  const searchInput = document.getElementById('filter-search')
  
  statusSelect.addEventListener('change', (e) => {
    currentFilters.status = e.target.value
    loadGames()
  })
  
  userSelect.addEventListener('change', (e) => {
    currentFilters.user_id = e.target.value
    loadGames()
  })
  
  searchInput.addEventListener('input', (e) => {
    currentFilters.search = e.target.value
    if (searchTimeout) clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => loadGames(), 300)
  })
}

function setupTableActions() {
  const tbody = document.getElementById('games-tbody')
  tbody.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]')
    if (!btn) return
    
    const action = btn.dataset.action
    const gameId = btn.dataset.gameId
    const gameName = btn.dataset.gameName
    
    if (action === 'end-game') {
      handleEndGame(gameId, gameName)
    } else if (action === 'view-players') {
      openPlayersModal(gameId, gameName)
    }
  })
}

async function handleEndGame(gameId, gameName) {
  // Close any open modals before showing confirmation
  const membersModal = document.getElementById('players-modal')
  if (membersModal && !membersModal.hidden) {
    membersModal.hidden = true
  }
  
  await showConfirmModal({
    title: 'End Game Session',
    message: `Are you sure you want to end the game <strong>"${gameName}"</strong>? This action cannot be undone and will end the session for all players.`,
    confirmText: 'End Game',
    iconType: 'leave',
    iconClass: 'modal-icon-warning',
    onConfirm: async () => {
      try {
        const response = await fetchWithAuth(`/api/v1/admin/games/${gameId}/end`, {
          method: 'POST'
        })
        
        if (!response.ok) throw new Error('Failed to end game')
        
        showMessage(`Game "${gameName}" ended successfully`, 'success')
        loadGames()
      } catch (error) {
        showMessage(error.message, 'error')
      }
    }
  })
}

async function openPlayersModal(gameId, gameName) {
  const modal = document.getElementById('players-modal')
  const subtitle = document.getElementById('modal-subtitle')
  const listContainer = document.getElementById('players-list')
  const loading = document.getElementById('players-list-loading')
  
  if (!modal || !subtitle || !listContainer || !loading) {
    console.error('Modal elements not found')
    return
  }
  
  subtitle.textContent = `Members of "${gameName}"`
  listContainer.innerHTML = ''
  loading.hidden = false
  modal.hidden = false
  
  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/members`)
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to load members')
    }
    
    const data = await response.json()
    console.log('Members response:', data)
    
    // El endpoint devuelve un array directamente, no un objeto con propiedad "members"
    const members = Array.isArray(data) ? data : (data.members || [])
    
    loading.hidden = true
    
    if (members.length === 0) {
      listContainer.innerHTML = '<p class="text-muted" style="text-align: center; padding: 2rem;">No members found</p>'
    } else {
      renderPlayersList(gameId, gameName, members)
    }
  } catch (error) {
    console.error('Error loading members:', error)
    loading.hidden = true
    listContainer.innerHTML = `<p class="text-error">${error.message}</p>`
  }
}

function renderPlayersList(gameId, gameName, members) {
  const listContainer = document.getElementById('players-list')
  
  if (!listContainer) {
    console.error('Players list container not found')
    return
  }
  
  console.log('Rendering players:', members)
  
  listContainer.innerHTML = members.map(member => {
    const isDM = member.membership?.role_in_game === 'DM' || member.role_in_game === 'DM'
    const isKicked = member.membership?.status === 'KICKED' || member.status === 'KICKED'
    const isActive = member.membership?.status === 'ACTIVE' || member.status === 'ACTIVE'
    
    return `
      <div class="player-item">
        <div class="player-info">
          <div class="player-name-row">
            <span class="player-name">${escapeHtml(member.name)}</span>
            <span class="role-badge ${isDM ? 'role-dm' : 'role-player'}">${isDM ? 'DM' : 'Player'}</span>
          </div>
          <span class="player-username">@${escapeHtml(member.username || member.user_id)}</span>
        </div>
        <div class="player-actions">
          ${isKicked ? `
            <span class="membership-kicked-badge">Kicked</span>
          ` : isActive ? `
            <button class="btn-sm-danger" 
              data-kick-user-id="${member.user_id}" 
              data-username="${escapeHtml(member.username || member.name)}"
              data-is-dm="${isDM}">
              Kick
            </button>
          ` : `
            <span class="text-muted">${member.status || 'LEFT'}</span>
          `}
        </div>
      </div>
    `
  }).join('')
  
  setupKickActions(gameId, gameName)
}

function setupKickActions(gameId, gameName) {
  const listContainer = document.getElementById('players-list')
  listContainer.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-kick-user-id]')
    if (!btn) return
    
    const userId = btn.dataset.kickUserId
    const username = btn.dataset.username
    const isDM = btn.dataset.isDm === 'true'
    
    handleKickPlayer(gameId, gameName, userId, username, isDM)
  })
}

async function handleKickPlayer(gameId, gameName, userId, username, isDM) {
  // Hide members modal before showing confirmation
  const membersModal = document.getElementById('players-modal')
  if (membersModal) {
    membersModal.hidden = true
  }
  
  const title = isDM ? 'Kick Dungeon Master' : 'Kick Player'
  const message = isDM 
    ? `⚠️ <strong>WARNING:</strong> You are about to kick the Dungeon Master <strong>@${username}</strong>. This will automatically <strong>END</strong> the game session for everyone.`
    : `Are you sure you want to kick <strong>@${username}</strong> from the game "${gameName}"?`
  
  await showConfirmModal({
    title,
    message,
    confirmText: 'Kick User',
    iconType: 'leave',
    iconClass: 'modal-icon-warning',
    onConfirm: async () => {
      try {
        const response = await fetchWithAuth(`/api/v1/admin/games/${gameId}/kick-member`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: parseInt(userId) })
        })
        
        if (!response.ok) throw new Error('Failed to kick user')
        
        const result = await response.json()
        const successMsg = result.game_ended 
          ? `User kicked and game "${gameName}" ended`
          : `User @${username} kicked successfully`
          
        showMessage(successMsg, 'success')
        loadGames()
      } catch (error) {
        showMessage(error.message, 'error')
        // Re-show members modal if kick failed
        if (membersModal) {
          membersModal.hidden = false
        }
      }
    },
    onCancel: () => {
      // Re-show members modal if user cancels
      if (membersModal) {
        membersModal.hidden = false
      }
    }
  })
}

function setupModal() {
  const modal = document.getElementById('players-modal')
  if (!modal) {
    console.error('Players modal not found')
    return
  }
  
  const closeBtn = document.getElementById('close-players-modal')
  const overlay = modal.querySelector('.modal-overlay')
  
  const closeModalFunc = () => {
    modal.hidden = true
  }
  
  if (closeBtn) {
    closeBtn.addEventListener('click', closeModalFunc)
  }
  
  if (overlay) {
    overlay.addEventListener('click', closeModalFunc)
  }
  
  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) {
      closeModalFunc()
    }
  })
  
  window.closeModal = closeModalFunc
}

function closeModal() {
  const modal = document.getElementById('players-modal')
  if (modal) modal.hidden = true
}

function showMessage(message, type = 'info') {
  const messageEl = document.getElementById('admin-message')
  messageEl.textContent = message
  messageEl.className = `admin-message admin-message-${type}`
  messageEl.hidden = false
  
  setTimeout(() => {
    messageEl.hidden = true
  }, 5000)
}
