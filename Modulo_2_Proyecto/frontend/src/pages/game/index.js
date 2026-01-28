/**
 * Main game page coordinator
 * Orchestrates all game-related modules
 */
import template from '../game.html?raw'
import { Footer } from '../../components/index.js'
import { getRouteParams, onBeforeRouteChange } from '../../router.js'
import { getUserFromToken } from '../../infrastructure/auth/auth.js'
import { fetchWithAuth, escapeHtml, getInitials } from '../../utils/index.js'
import { gameState, resetGameState } from './game-state.js'
import { 
  initChatComponent, 
  disconnectChat, 
  setupClearTurnButton, 
  initNPCManager 
} from './game-turns.js'
import { 
  loadPlayers, 
  setupLeaveButton, 
  loadInviteCode, 
  setupCopyInviteButton 
} from './game-players.js'
import { loadUserCharacter } from './game-character.js'
import { 
  loadPendingCharacters, 
  setupCharacterSubmissionListener 
} from './game-dm-characters.js'

/**
 * Main entry point for the game page
 */
export function gamePage(app) {
  app.innerHTML = template + Footer()
  initGame()
}

/**
 * Initialize the game page
 */
async function initGame() {
  const { id: gameId } = getRouteParams()
  
  if (!gameId) {
    showError('Invalid game ID')
    return
  }

  gameState.currentUser = getUserFromToken()
  await loadGame(gameId)
}

/**
 * Load game data and setup the page
 */
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
    gameState.currentGame = game

    loadingEl.hidden = true
    contentEl.hidden = false

    renderGameInfo(game)
    setupGameActions(game)
    await loadPlayers(gameId, showMessage)
    await loadUserCharacter(gameId)
    
    // Set up history link
    const historyLink = document.getElementById('view-history-link')
    if (historyLink) {
      historyLink.href = `/game/${gameId}/history`
    }

    // Set up notes link
    const notesLink = document.getElementById('view-notes-link')
    if (notesLink) {
      notesLink.href = `/game/${gameId}/notes`
    }
    
    initChatComponent(gameId, showMessage)

    // Setup character event listeners for DM
    if (gameState.currentUserRole === 'DM') {
      setupCharacterSubmissionListener(showMessage)
    }

    // Setup message listeners for character approval/rejection
    setupCharacterMessageListeners()
    
    // Setup global message listener
    setupGlobalMessageListener()
    
    // Setup reload players listener
    setupReloadPlayersListener(gameId)

  } catch (error) {
    loadingEl.hidden = true
    showError(error.message)
  }
}

/**
 * Render game information header
 */
function renderGameInfo(game) {
  const user = getUserFromToken()
  const isDM = game.dm_user_id.toString() === user?.sub.toString()
  gameState.currentUserRole = isDM ? 'DM' : 'PLAYER'

  document.getElementById('game-name').textContent = game.name
  
  const statusBadge = document.getElementById('game-status')
  statusBadge.textContent = game.status
  statusBadge.className = `game-status-badge ${game.status === 'ACTIVE' ? 'status-active' : 'status-ended'}`
  
  const roleBadge = document.getElementById('game-role')
  roleBadge.textContent = isDM ? 'Dungeon Master' : 'Player'
  roleBadge.className = `game-role-badge ${isDM ? 'role-dm' : 'role-player'}`

  const dmSection = document.getElementById('dm-section')
  const npcSection = document.getElementById('npc-section')
  if (isDM) {
    dmSection.hidden = false
    npcSection.hidden = false
    loadInviteCode(game.id)
    setupCopyInviteButton(showMessage)
    initNPCManager(
      game.id,
      null, // onNPCCreated
      null, // onNPCUpdated
      null, // onNPCDeleted
      (msg) => showMessage(msg, 'error'),
      (msg) => showMessage(msg, 'success')
    )
    loadPendingCharacters(game.id)
    setupClearTurnButton()
    
    // Setup clear turn button with message handler
    const clearTurnBtn = document.getElementById('clear-turn-btn')
    if (clearTurnBtn) {
      const originalHandler = clearTurnBtn.onclick
      clearTurnBtn.onclick = null
      clearTurnBtn.addEventListener('click', () => {
        if (gameState.gameChat?.socketClient && gameState.currentGame) {
          gameState.gameChat.socketClient.clearTurn(gameState.currentGame.id)
          showMessage('Turn order ended', 'success')
        }
      })
    }
  }

  const leaveBtn = document.getElementById('leave-game-btn')
  leaveBtn.hidden = false
  setupLeaveButton(game.id, showMessage)
}

/**
 * Setup game-related event handlers
 */
function setupGameActions(game) {
  window.addEventListener('beforeunload', disconnectChat)
  
  gameState.unsubscribeRouteChange = onBeforeRouteChange(() => {
    cleanupGamePage()
  })
}

/**
 * Cleanup when leaving the game page
 */
function cleanupGamePage() {
  disconnectChat()
  
  if (gameState.characterCreator) {
    gameState.characterCreator.destroy()
    gameState.characterCreator = null
  }
  
  if (gameState.npcManager) {
    gameState.npcManager.destroy()
    gameState.npcManager = null
  }
  
  if (gameState.unsubscribeRouteChange) {
    gameState.unsubscribeRouteChange()
    gameState.unsubscribeRouteChange = null
  }
  
  window.removeEventListener('beforeunload', disconnectChat)
  
  // Reset all game state
  resetGameState()
}

/**
 * Setup listeners for character approval/rejection messages
 */
function setupCharacterMessageListeners() {
  window.addEventListener('character:approved', (event) => {
    showMessage(event.detail.message, 'success')
  })

  window.addEventListener('character:rejected', (event) => {
    showMessage(event.detail.message, 'error')
  })
}

/**
 * Setup global message listener for all modules
 */
function setupGlobalMessageListener() {
  window.addEventListener('game:message', (event) => {
    const { message, type } = event.detail
    showMessage(message, type)
  })
}

/**
 * Setup listener to reload players list
 */
function setupReloadPlayersListener(gameId) {
  window.addEventListener('game:reload-players', async () => {
    await loadPlayers(gameId, showMessage)
  })
}

/**
 * Show an error message
 */
function showError(message) {
  const loadingEl = document.getElementById('game-loading')
  const errorEl = document.getElementById('game-error')
  const errorMsgEl = document.getElementById('game-error-message')
  
  loadingEl.hidden = true
  errorEl.hidden = false
  errorMsgEl.textContent = message
}

/**
 * Show a temporary message notification
 */
function showMessage(message, type = 'info') {
  const messageEl = document.getElementById('game-message')
  messageEl.textContent = message
  messageEl.className = `game-message game-message-${type}`
  messageEl.hidden = false

  setTimeout(() => {
    messageEl.hidden = true
  }, 3000)
}
