/**
 * Turn management and real-time communication
 */
import { GameChat } from '../../components/index.js'
import { NPCManager } from '../../components/index.js'
import { gameState } from './game-state.js'
import { registerCharacterEventListeners } from './game-character.js'

/**
 * Initialize the game chat component
 */
export function initChatComponent(gameId, onMessage) {
  const isDM = gameState.currentUserRole === 'DM'
  
  gameState.gameChat = new GameChat({
    gameId,
    isDM,
    onError: (message) => onMessage(message, 'error'),
    onConnected: () => {
      // Register character event listeners when socket is connected
      registerCharacterEventListeners()
      // Register turn management listeners
      registerTurnEventListeners()
      // Update NPCManager with socket client
      if (gameState.npcManager && gameState.gameChat?.socketClient) {
        gameState.npcManager.setSocketClient(gameState.gameChat.socketClient)
      }
    }
  })

  gameState.gameChat.init()
  
  // Also register turn listeners immediately after init (in case already connected)
  // Use a small delay to ensure socket client is set up
  setTimeout(() => {
    if (gameState.gameChat?.socketClient && !gameState.gameChat.socketClient.eventHandlers.has('turn_update')) {
      console.log('[Game] Registering turn listeners (delayed fallback)')
      registerTurnEventListeners()
    }
    // Update NPCManager with socket client (fallback)
    if (gameState.npcManager && gameState.gameChat?.socketClient) {
      gameState.npcManager.setSocketClient(gameState.gameChat.socketClient)
    }
  }, 1000)
}

/**
 * Disconnect from chat and cleanup
 */
export function disconnectChat() {
  if (gameState.gameChat) {
    gameState.gameChat.leaveChat()
    gameState.gameChat.disconnect()
    gameState.gameChat = null
  }
}

/**
 * Register turn-related event listeners
 */
function registerTurnEventListeners() {
  if (!gameState.gameChat?.socketClient) {
    console.warn('[Game] Cannot register turn events: no socket client')
    return
  }

  const socket = gameState.gameChat.socketClient

  socket.on('turn_update', (data) => {
    console.log('[Game] Turn update received:', data)
    
    // Support both USER and NPC turns
    if (data.turn_type === 'USER' && data.user_id) {
      gameState.currentTurn = {
        turn_type: 'USER',
        user_id: data.user_id,
        character_name: data.character_name,
        set_by: data.set_by
      }
    } else if (data.turn_type === 'NPC' && data.npc_id) {
      gameState.currentTurn = {
        turn_type: 'NPC',
        npc_id: data.npc_id,
        character_name: data.character_name,
        npc_type: data.npc_type,
        set_by: data.set_by
      }
    } else {
      // Clear turn (backwards compatibility with old data.user_id check)
      gameState.currentTurn = null
    }
    
    updateTurnBanner()
    
    // Notify chat component to update dice button state
    if (gameState.gameChat) {
      gameState.gameChat.onTurnUpdate(gameState.currentTurn)
    }
  })

  console.log('[Game] Turn event listeners registered')
}

/**
 * Update the turn banner UI
 */
export function updateTurnBanner() {
  console.log('[Game] updateTurnBanner called', { 
    currentTurn: gameState.currentTurn, 
    currentUser: gameState.currentUser, 
    currentUserRole: gameState.currentUserRole 
  })
  
  const banner = document.getElementById('turn-banner')
  const message = document.getElementById('turn-message')
  const clearBtn = document.getElementById('clear-turn-btn')

  if (!banner || !message || !clearBtn) {
    console.warn('[Game] Turn banner elements not found in DOM')
    return
  }

  if (!gameState.currentTurn) {
    // No active turn
    console.log('[Game] No active turn, hiding banner')
    banner.hidden = true
    banner.classList.remove('turn-banner-active', 'turn-banner-npc')
    return
  }

  // Show banner
  banner.hidden = false
  
  if (gameState.currentTurn.turn_type === 'NPC') {
    // NPC Turn
    console.log('[Game] Showing turn banner for NPC:', gameState.currentTurn.npc_id)
    
    const displayName = gameState.currentTurn.character_name || 'Unknown NPC'
    const npcType = gameState.currentTurn.npc_type || 'NPC'
    
    message.textContent = `${displayName} (NPC - ${npcType})`
    banner.classList.remove('turn-banner-active')
    banner.classList.add('turn-banner-npc')
    
    // Show clear button only for DM
    clearBtn.hidden = gameState.currentUserRole !== 'DM'
    
  } else if (gameState.currentTurn.turn_type === 'USER') {
    // USER Turn
    console.log('[Game] Showing turn banner for user:', gameState.currentTurn.user_id)
    
    const displayName = gameState.currentTurn.character_name || 'Unknown Player'
    
    // Check if it's the current user's turn
    const isMyTurn = gameState.currentUser && 
      String(gameState.currentTurn.user_id) === String(gameState.currentUser.sub)
    
    console.log('[Game] Is my turn?', isMyTurn, 'currentTurn.user_id:', gameState.currentTurn.user_id, 'currentUser.sub:', gameState.currentUser?.sub)
    
    if (isMyTurn) {
      message.textContent = `It's your turn!`
      banner.classList.add('turn-banner-active')
      banner.classList.remove('turn-banner-npc')
    } else {
      message.textContent = `${displayName}'s turn`
      banner.classList.remove('turn-banner-active', 'turn-banner-npc')
    }

    // Show clear button only for DM
    clearBtn.hidden = gameState.currentUserRole !== 'DM'
  }
  
  console.log('[Game] Banner updated successfully')
}

/**
 * Setup the clear turn button (DM only)
 */
export function setupClearTurnButton() {
  const clearBtn = document.getElementById('clear-turn-btn')
  
  clearBtn.addEventListener('click', () => {
    if (gameState.gameChat?.socketClient && gameState.currentGame) {
      gameState.gameChat.socketClient.clearTurn(gameState.currentGame.id)
      // Show message is handled by caller
    }
  })
}

/**
 * Setup turn buttons for each player
 */
export function setupTurnButtons(gameId, onMessage) {
  const turnButtons = document.querySelectorAll('.btn-set-turn')
  
  turnButtons.forEach(button => {
    button.addEventListener('click', (event) => {
      event.stopPropagation()
      const userId = parseInt(button.dataset.userId)
      const characterName = button.dataset.characterName
      handleSetTurn(gameId, userId, characterName, onMessage)
    })
  })
}

/**
 * Handle setting turn for a specific user
 */
function handleSetTurn(gameId, userId, characterName, onMessage) {
  if (gameState.gameChat?.socketClient) {
    gameState.gameChat.socketClient.setTurn(gameId, userId, characterName)
    if (onMessage) onMessage(`Turn assigned to ${characterName}`, 'success')
  } else {
    if (onMessage) onMessage('Not connected to game', 'error')
  }
}

/**
 * Initialize NPC Manager component
 */
export function initNPCManager(gameId, onNPCCreated, onNPCUpdated, onNPCDeleted, onError, onSuccess) {
  gameState.npcManager = new NPCManager({
    gameId,
    socketClient: gameState.gameChat?.socketClient,
    onNPCCreated: (npc) => {
      console.log('NPC created:', npc)
      if (onNPCCreated) onNPCCreated(npc)
    },
    onNPCUpdated: (npc) => {
      console.log('NPC updated:', npc)
      if (onNPCUpdated) onNPCUpdated(npc)
    },
    onNPCDeleted: (npcId) => {
      console.log('NPC deleted:', npcId)
      if (onNPCDeleted) onNPCDeleted(npcId)
    },
    onError,
    onSuccess
  })
  
  gameState.npcManager.init()
}
