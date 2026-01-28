/**
 * Player management and membership
 */
import { showConfirmModal } from '../../components/index.js'
import { navigate } from '../../router.js'
import { getUserFromToken } from '../../infrastructure/auth/auth.js'
import { fetchWithAuth, escapeHtml, getInitials } from '../../utils/index.js'
import { gameState } from './game-state.js'
import { disconnectChat } from './game-turns.js'
import { setupTurnButtons } from './game-turns.js'

/**
 * Load and render the list of players in the game
 */
export async function loadPlayers(gameId, onMessage) {
  const loadingEl = document.getElementById('players-loading')
  const listEl = document.getElementById('players-list')
  const countEl = document.getElementById('players-count')

  const user = getUserFromToken()
  const membersResponse = await fetchWithAuth(`/api/v1/game/${gameId}/members`)
  if (!membersResponse.ok) {
    throw new Error('Failed to load current user')
  }
  const members = await membersResponse.json()
  
  loadingEl.hidden = true
  listEl.hidden = false
  
  countEl.textContent = `${members.length} member${members.length !== 1 ? 's' : ''}`
  const canKick = gameState.currentUserRole === 'DM'
  
  listEl.innerHTML = members.map(member => {
    const isDM = member.role_in_game === 'DM'
    const isCurrentUser = member.user_id.toString() === user?.sub.toString()
    const membershipStatus = member.status
    const isActive = membershipStatus === 'ACTIVE'
    const showKickButton = canKick && !isCurrentUser && !isDM && isActive
    const showTurnButton = gameState.currentUserRole === 'DM' && !isDM && isActive
    
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
        <div class="player-actions">
          ${showTurnButton ? `
            <button class="btn btn-ghost btn-sm btn-set-turn" 
                    data-user-id="${member.user_id}" 
                    data-character-name="${escapeHtml(member?.username || member?.name || 'Unknown')}"
                    title="Give turn to this player">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              Give Turn
            </button>
          ` : ''}
          ${showKickButton ? `
            <button class="btn btn-ghost btn-sm btn-kick" data-user-id="${member.user_id}" title="Kick player">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          ` : ''}
        </div>
      </div>
    `
  }).join('')

  setupKickButtons(gameId, onMessage)
  setupTurnButtons(gameId, onMessage)
}

/**
 * Setup kick buttons for each player
 */
function setupKickButtons(gameId, onMessage) {
  const kickButtons = document.querySelectorAll('.btn-kick')
  
  kickButtons.forEach(button => {
    button.addEventListener('click', async (event) => {
      event.stopPropagation()
      const userId = button.dataset.userId
      await handleKickUser(gameId, userId, onMessage)
    })
  })
}

/**
 * Handle kicking a user from the game
 */
async function handleKickUser(gameId, userId, onMessage) {
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
      onMessage('Player kicked successfully', 'success')
      await loadPlayers(gameId, onMessage)
    }
  } catch (error) {
    onMessage(error.message, 'error')
  }
}

/**
 * Setup the leave game button
 */
export function setupLeaveButton(gameId, onMessage) {
  const leaveBtn = document.getElementById('leave-game-btn')
  const user = getUserFromToken()

  leaveBtn.addEventListener('click', () => {
    showLeaveModal(gameId, user, onMessage)
  })
}

/**
 * Show the leave/end game modal
 */
async function showLeaveModal(gameId, user, onMessage) {
  const isDM = gameState.currentUserRole === 'DM'

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
    onMessage(error.message, 'error')
  }
}

/**
 * Load and display the invite code (DM only)
 */
export async function loadInviteCode(gameId) {
  const inviteCodeEl = document.getElementById('invite-code')
  
  try {
    inviteCodeEl.textContent = 'Ask your DM for the invite code'
  } catch (error) {
    inviteCodeEl.textContent = 'Unable to load'
  }
}

/**
 * Setup the copy invite code button
 */
export function setupCopyInviteButton(onMessage) {
  const copyBtn = document.getElementById('copy-invite-btn')
  const inviteCodeEl = document.getElementById('invite-code')

  copyBtn.addEventListener('click', async () => {
    const code = inviteCodeEl.textContent
    if (code && code !== 'Loading...' && code !== 'Unable to load') {
      try {
        await navigator.clipboard.writeText(code)
        onMessage('Invite code copied!', 'success')
      } catch {
        onMessage('Failed to copy', 'error')
      }
    }
  })
}
