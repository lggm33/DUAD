import template from './game.html?raw'
import {
  Footer,
  showConfirmModal,
  GameChat,
  CharacterCreator,
  CharacterSheet,
  NPCManager,
  CombatTracker,
  CombatLog,
  EncounterBuilder,
  ReconnectOverlay,
  ActionPanel
} from '../components/index.js'
import { navigate, getRouteParams, onBeforeRouteChange } from '../router.js'
import { getUserFromToken } from '../infrastructure/auth/auth.js'
import { fetchWithAuth, escapeHtml, getInitials } from '../utils/index.js'

let currentGame = null
let currentUserRole = null
let gameChat = null
let currentUser = null
let unsubscribeRouteChange = null
let characterCreator = null
let characterSheet = null
let currentCharacter = null
let npcManager = null
let combatTracker = null
let combatLog = null
let encounterBuilder = null
let reconnectOverlay = null
let actionPanel = null

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
    await loadUserCharacter(gameId)
    
    initChatComponent(gameId)
    
    // Initialize reconnect overlay for connection loss handling
    initReconnectOverlay()
    
    // Check for active encounter and initialize combat tracker
    await checkActiveEncounter(gameId)

  } catch (error) {
    loadingEl.hidden = true
    showError(error.message)
  }
}

function initChatComponent(gameId) {
  gameChat = new GameChat({
    gameId,
    onError: (message) => showMessage(message, 'error')
  })
  
  gameChat.init()
  
  // Register character event listeners after a short delay to ensure socket is ready
  setTimeout(() => {
    registerCharacterEventListeners()
  }, 500)
}

function registerCharacterEventListeners() {
  if (!gameChat?.socketClient) {
    console.warn('[Game] Cannot register character events: no socket client')
    return
  }

  const socket = gameChat.socketClient

  // Listen for new character submissions (DM only)
  socket.on('character:submitted', (data) => {
    console.log('[Game] Character submitted:', data)
    if (currentUserRole === 'DM') {
      showMessage(`New character "${data.character_name}" submitted by ${data.player_name}`, 'info')
      addPendingCharacter({
        id: data.character_id,
        name: data.character_name,
        user_id: data.user_id,
        game_id: data.game_id,
        data: {}
      })
    }
  })

  // Listen for character approval (Player)
  socket.on('character:approved', (data) => {
    console.log('[Game] Character approved event received:', data)
    console.log('[Game] currentUser:', currentUser)
    console.log('[Game] currentCharacter:', currentCharacter)
    console.log('[Game] Comparing user_id:', data.user_id, 'with currentUser.sub:', currentUser?.sub)
    
    if (currentUser && String(data.user_id) === String(currentUser.sub)) {
      console.log('[Game] User ID matched! Updating UI...')
      showMessage('Your character has been approved! You can now fully participate.', 'success')
      if (currentCharacter && currentCharacter.id === data.character_id) {
        currentCharacter.status = 'APPROVED'
        currentCharacter.dm_feedback = data.feedback
        renderCharacterSection(currentCharacter)
      } else {
        // Reload character if we don't have it or ID doesn't match
        console.log('[Game] Reloading character from server...')
        loadUserCharacter(currentGame.id)
      }
    }
  })

  // Listen for character rejection (Player)
  socket.on('character:rejected', (data) => {
    console.log('[Game] Character rejected event received:', data)
    console.log('[Game] currentUser:', currentUser)
    
    if (currentUser && String(data.user_id) === String(currentUser.sub)) {
      console.log('[Game] User ID matched! Showing rejection...')
      showMessage('The DM has requested changes to your character.', 'error')
      if (currentCharacter && currentCharacter.id === data.character_id) {
        currentCharacter.status = 'REJECTED'
        currentCharacter.dm_feedback = data.feedback
        renderCharacterSection(currentCharacter)
      } else {
        // Reload character if we don't have it
        loadUserCharacter(currentGame.id)
      }
    }
  })

  console.log('[Game] Character event listeners registered on socket:', socket)
}

function initNPCManager(gameId) {
  npcManager = new NPCManager({
    gameId,
    onNPCCreated: (npc) => {
      console.log('NPC created:', npc)
    },
    onNPCUpdated: (npc) => {
      console.log('NPC updated:', npc)
    },
    onNPCDeleted: (npcId) => {
      console.log('NPC deleted:', npcId)
    },
    onError: (message) => showMessage(message, 'error'),
    onSuccess: (message) => showMessage(message, 'success')
  })
  
  npcManager.init()
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

  const dmSection = document.getElementById('dm-section')
  const npcSection = document.getElementById('npc-section')
  if (isDM) {
    dmSection.hidden = false
    npcSection.hidden = false
    loadInviteCode(game.id)
    setupCopyInviteButton()
    setupEncounterButton()
    initNPCManager(game.id)
    loadPendingCharacters(game.id)
  }

  const leaveBtn = document.getElementById('leave-game-btn')
  leaveBtn.hidden = false
  setupLeaveButton(game.id)
}

async function loadInviteCode(gameId) {
  const inviteCodeEl = document.getElementById('invite-code')
  
  try {
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

function setupEncounterButton() {
  const createEncounterBtn = document.getElementById('create-encounter-btn')
  
  if (createEncounterBtn) {
    createEncounterBtn.addEventListener('click', () => {
      openEncounterBuilder()
    })
  }
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

  const user = getUserFromToken()
  const membersResponse = await fetchWithAuth(`/api/v1/game/${gameId}/members`)
  if (!membersResponse.ok) {
    throw new Error('Failed to load current user')
  }
  const members = await membersResponse.json()
  
  loadingEl.hidden = true
  listEl.hidden = false
  
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
  window.addEventListener('beforeunload', disconnectChat)
  
  unsubscribeRouteChange = onBeforeRouteChange(() => {
    cleanupGamePage()
  })
}

function cleanupGamePage() {
  disconnectChat()
  
  if (characterCreator) {
    characterCreator.destroy()
    characterCreator = null
  }
  
  if (npcManager) {
    npcManager.destroy()
    npcManager = null
  }
  
  if (combatTracker) {
    combatTracker.destroy()
    combatTracker = null
  }
  
  if (combatLog) {
    combatLog.destroy()
    combatLog = null
  }
  
  if (actionPanel) {
    actionPanel.destroy()
    actionPanel = null
  }
  
  if (encounterBuilder) {
    encounterBuilder.destroy()
    encounterBuilder = null
  }
  
  if (reconnectOverlay) {
    reconnectOverlay.destroy()
    reconnectOverlay = null
  }
  
  if (unsubscribeRouteChange) {
    unsubscribeRouteChange()
    unsubscribeRouteChange = null
  }
  
  window.removeEventListener('beforeunload', disconnectChat)
}

// ========================================
// Combat Tracker Functions
// ========================================

/**
 * Check if there's an active encounter and initialize the combat tracker
 */
async function checkActiveEncounter(gameId) {
  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/encounters?status=ACTIVE`)
    
    if (!response.ok) {
      // No active encounters or endpoint not available
      return
    }
    
    const encounters = await response.json()
    
    if (encounters && encounters.length > 0) {
      const activeEncounter = encounters[0]
      initCombatTracker(activeEncounter.id)
    }
  } catch (error) {
    console.log('[Game] No active encounters or error checking:', error.message)
  }
}

/**
 * Initialize the combat tracker for an active encounter
 */
function initCombatTracker(encounterId) {
  if (combatTracker) {
    combatTracker.destroy()
  }
  
  if (!gameChat?.socketClient) {
    console.warn('[Game] Cannot init combat tracker: no socket client')
    return
  }
  
  combatTracker = new CombatTracker({
    encounterId: encounterId,
    socketClient: gameChat.socketClient,
    gameId: currentGame.id,
    currentUserRole: currentUserRole,
    currentCharacterId: currentCharacter?.id || null,
    onTurnChange: (combatant, isMyTurn) => {
      if (isMyTurn) {
        showMessage('It\'s your turn!', 'info')
      }
    },
    onEncounterEnd: (data) => {
      showMessage(`Encounter ended: ${data.outcome}`, 'success')
      stopCombatTracking()
    }
  })
  
  combatTracker.init()
  
  // Initialize combat log alongside tracker
  initCombatLog(encounterId)
  
  // Initialize action panel for players
  initActionPanel(encounterId)
  
  // Update reconnect overlay with active encounter
  if (reconnectOverlay) {
    reconnectOverlay.setActiveEncounterId(encounterId)
  }
}

/**
 * Initialize the combat log for an active encounter
 */
function initCombatLog(encounterId) {
  if (combatLog) {
    combatLog.destroy()
  }
  
  if (!gameChat?.socketClient) {
    console.warn('[Game] Cannot init combat log: no socket client')
    return
  }
  
  combatLog = new CombatLog({
    encounterId: encounterId,
    gameId: currentGame.id,
    socketClient: gameChat.socketClient,
    onError: (message) => showMessage(message, 'error')
  })
  
  combatLog.init()
  
  // Show the combat log container
  const combatLogContainer = document.getElementById('combat-log-container')
  if (combatLogContainer) {
    combatLogContainer.hidden = false
  }
}

/**
 * Initialize the action panel for player combat actions
 */
function initActionPanel(encounterId) {
  // Only initialize for players, not DMs
  if (currentUserRole === 'DM') {
    return
  }
  
  if (actionPanel) {
    actionPanel.destroy()
  }
  
  if (!gameChat?.socketClient) {
    console.warn('[Game] Cannot init action panel: no socket client')
    return
  }
  
  if (!currentCharacter) {
    console.warn('[Game] Cannot init action panel: no character')
    return
  }
  
  actionPanel = new ActionPanel({
    encounterId: encounterId,
    characterId: currentCharacter.id,
    socketClient: gameChat.socketClient,
    gameId: currentGame.id,
    characterData: currentCharacter.data || {},
    onActionSubmitted: (actionData) => {
      console.log('[Game] Action submitted:', actionData)
    },
    onTargetHighlight: (combatantKey, shouldHighlight) => {
      // Highlight targets in combat tracker
      if (combatTracker && combatTracker.highlightCombatant) {
        combatTracker.highlightCombatant(combatantKey, shouldHighlight)
      }
    },
    getCombatants: () => {
      // Return current combatants from combat tracker
      if (combatTracker && combatTracker.initiativeOrder) {
        return combatTracker.initiativeOrder.map((c) => ({
          ...c,
          state: combatTracker.combatantsState?.[c.key] || {}
        }))
      }
      return []
    }
  })
  
  actionPanel.init()
}

/**
 * Initialize the reconnect overlay for connection loss handling
 */
function initReconnectOverlay() {
  if (reconnectOverlay) {
    reconnectOverlay.destroy()
  }
  
  if (!gameChat?.socketClient) {
    console.warn('[Game] Cannot init reconnect overlay: no socket client')
    return
  }
  
  reconnectOverlay = new ReconnectOverlay({
    socketClient: gameChat.socketClient,
    onReconnected: () => {
      showMessage('Connection restored!', 'success')
    },
    onReturnToDashboard: () => {
      navigate('/dashboard')
    },
    activeEncounterId: null
  })
  
  reconnectOverlay.init()
}

/**
 * Public function to start tracking an encounter (called from other components)
 */
function startCombatTracking(encounterId) {
  initCombatTracker(encounterId)
}

/**
 * Public function to stop tracking combat
 */
function stopCombatTracking() {
  if (combatTracker) {
    combatTracker.destroy()
    combatTracker = null
  }
  
  if (combatLog) {
    combatLog.destroy()
    combatLog = null
  }
  
  if (actionPanel) {
    actionPanel.destroy()
    actionPanel = null
  }
  
  // Hide the combat log container
  const combatLogContainer = document.getElementById('combat-log-container')
  if (combatLogContainer) {
    combatLogContainer.hidden = true
  }
  
  // Clear active encounter from reconnect overlay
  if (reconnectOverlay) {
    reconnectOverlay.setActiveEncounterId(null)
  }
}

// ========================================
// Encounter Builder Functions
// ========================================

/**
 * Open the encounter builder modal (DM only)
 */
function openEncounterBuilder(encounterId = null) {
  if (currentUserRole !== 'DM') {
    showMessage('Only the DM can create encounters', 'error')
    return
  }
  
  if (encounterBuilder) {
    encounterBuilder.destroy()
  }
  
  encounterBuilder = new EncounterBuilder({
    gameId: currentGame.id,
    encounterId: encounterId,
    onSave: (encounter) => {
      showMessage('Encounter saved successfully!', 'success')
      encounterBuilder = null
    },
    onActivate: async (encounterId) => {
      await activateEncounter(encounterId)
    },
    onCancel: () => {
      encounterBuilder = null
    }
  })
  
  encounterBuilder.init()
}

/**
 * Activate an encounter and start combat
 */
async function activateEncounter(encounterId) {
  try {
    const response = await fetchWithAuth(
      `/api/v1/game/${currentGame.id}/encounter/${encounterId}/activate`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }
    )
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to activate encounter')
    }
    
    showMessage('Encounter activated! Rolling initiative...', 'success')
    
    // Initialize combat tracking for the active encounter
    initCombatTracker(encounterId)
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

/**
 * Expose functions for external use (e.g., from NPC Manager)
 */
window.gamePageActions = {
  openEncounterBuilder,
  startCombatTracking,
  stopCombatTracking
}

function disconnectChat() {
  if (gameChat) {
    gameChat.leaveChat()
    gameChat.disconnect()
    gameChat = null
  }
}

// ========================================
// Character Functions
// ========================================

async function loadUserCharacter(gameId) {
  // Only load character for players, not DMs
  if (currentUserRole === 'DM') {
    return
  }

  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/my-character`)
    
    if (response.ok) {
      const character = await response.json()
      currentCharacter = character
      console.log('[Game] Character loaded:', character.name, 'Status:', character.status)
      renderCharacterSection(character)
    } else if (response.status === 404) {
      // No character exists, show create prompt
      currentCharacter = null
      renderNoCharacterSection()
    }
  } catch (error) {
    console.error('[Game] Failed to load character:', error)
    renderNoCharacterSection()
  }
}

function renderCharacterSection(character) {
  const contentEl = document.getElementById('game-content')
  if (!contentEl) return

  // Remove existing character section if any
  const existingSection = document.getElementById('character-section')
  if (existingSection) {
    existingSection.remove()
  }

  const statusClass = getCharacterStatusClass(character.status)
  const statusText = formatCharacterStatus(character.status)
  const charData = character.data || {}

  const statusBanner = getCharacterStatusBanner(character)
  
  const sectionHtml = `
    <section id="character-section" class="game-section character-section">
      <div class="section-header">
        <div class="section-header-left">
          <h2 class="section-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            Your Character
          </h2>
        </div>
        <div class="section-header-right">
          <button id="view-full-sheet-btn" class="btn btn-ghost btn-sm" type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            View Full Sheet
          </button>
          <span class="character-status-badge ${statusClass}">${statusText}</span>
        </div>
      </div>

      ${statusBanner}
      
      <div class="character-card">
        <div class="character-avatar">
          <span>${getInitials(character.name)}</span>
        </div>
        <div class="character-info">
          <h3 class="character-name">${escapeHtml(character.name)}</h3>
          <p class="character-details">
            ${escapeHtml(charData.race || '???')} ${escapeHtml(charData.class || '???')} • Level ${charData.level || 1}
          </p>
        </div>
        <div class="character-stats">
          <div class="character-stat">
            <span class="character-stat-value">${charData.hp || 10}</span>
            <span class="character-stat-label">HP</span>
          </div>
          <div class="character-stat">
            <span class="character-stat-value">${charData.ac || 10}</span>
            <span class="character-stat-label">AC</span>
          </div>
        </div>
        ${character.status === 'DRAFT' || character.status === 'REJECTED' ? `
          <button id="edit-character-btn" class="btn btn-ghost">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Edit
          </button>
        ` : ''}
      </div>
    </section>
  `

  // Insert after chat section
  const chatSection = contentEl.querySelector('.chat-section')
  if (chatSection) {
    chatSection.insertAdjacentHTML('afterend', sectionHtml)
  } else {
    // Fallback: insert at beginning if chat section not found
    contentEl.insertAdjacentHTML('afterbegin', sectionHtml)
  }

  // Setup edit button if exists
  const editBtn = document.getElementById('edit-character-btn')
  if (editBtn) {
    editBtn.addEventListener('click', () => openCharacterCreator())
  }

  // Setup view full sheet button
  const viewSheetBtn = document.getElementById('view-full-sheet-btn')
  if (viewSheetBtn) {
    viewSheetBtn.addEventListener('click', () => showCharacterSheet())
  }
}

function renderNoCharacterSection() {
  const contentEl = document.getElementById('game-content')
  if (!contentEl) return

  // Remove existing character section if any
  const existingSection = document.getElementById('character-section')
  if (existingSection) {
    existingSection.remove()
  }

  const sectionHtml = `
    <section id="character-section" class="game-section character-section character-section-empty">
      <div class="section-header">
        <h2 class="section-title">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          Your Character
        </h2>
      </div>
      
      <div class="no-character-card">
        <div class="no-character-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
        </div>
        <h3>Create Your Character</h3>
        <p>You haven't created a character for this game yet. Create one to join the adventure!</p>
        <button id="create-character-btn" class="btn btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Create Character
        </button>
      </div>
    </section>
  `

  // Insert at the beginning of content
  const dmSection = document.getElementById('dm-section')
  if (dmSection && !dmSection.hidden) {
    dmSection.insertAdjacentHTML('afterend', sectionHtml)
  } else {
    const chatSection = contentEl.querySelector('.chat-section')
    if (chatSection) {
      chatSection.insertAdjacentHTML('beforebegin', sectionHtml)
    }
  }

  // Setup create button
  const createBtn = document.getElementById('create-character-btn')
  if (createBtn) {
    createBtn.addEventListener('click', () => openCharacterCreator())
  }
}

function openCharacterCreator() {
  if (characterCreator) {
    characterCreator.destroy()
  }

  const rules = currentGame?.custom_rules || currentGame?.ruleset_template?.base_rules || {}
  const isEditing = currentCharacter && currentCharacter.id

  characterCreator = new CharacterCreator({
    gameId: currentGame.id,
    characterId: isEditing ? currentCharacter.id : null,
    rules: rules,
    onSubmit: (character) => {
      const message = isEditing ? 'Character updated and submitted!' : 'Character submitted for approval!'
      showMessage(message, 'success')
      currentCharacter = character
      renderCharacterSection(character)
    },
    onSaveDraft: (character) => {
      const message = isEditing ? 'Character draft updated' : 'Character saved as draft'
      showMessage(message, 'success')
      currentCharacter = character
      renderCharacterSection(character)
    },
    onCancel: () => {
      // Nothing special needed
    }
  })

  // If editing existing character, pre-populate the data
  if (isEditing) {
    characterCreator.characterData = {
      name: currentCharacter.name || '',
      race: currentCharacter.data?.race || '',
      class: currentCharacter.data?.class || '',
      level: currentCharacter.data?.level || 1,
      background: currentCharacter.data?.background || '',
      stats: currentCharacter.data?.abilities || {
        STR: 10, DEX: 10, CON: 10, INT: 10, WIS: 10, CHA: 10
      },
      skills: currentCharacter.data?.skills || [],
      description: currentCharacter.data?.description || ''
    }
    characterCreator.recalculatePoints()
  }

  characterCreator.init()
}

function showCharacterSheet() {
  if (characterSheet) {
    characterSheet.destroy()
  }

  if (!currentCharacter) {
    showMessage('No character to display', 'error')
    return
  }

  // Only allow editing for APPROVED characters
  const isEditable = currentCharacter.status === 'APPROVED'

  characterSheet = new CharacterSheet({
    gameId: currentGame.id,
    characterId: currentCharacter.id,
    isEditable: isEditable,
    onUpdate: (character) => {
      currentCharacter = character
      renderCharacterSection(character)
      showMessage('Character updated successfully', 'success')
    },
    onClose: () => {
      characterSheet = null
    }
  })

  characterSheet.init()
}

function getCharacterStatusClass(status) {
  const classes = {
    'DRAFT': 'status-draft',
    'PENDING_APPROVAL': 'status-pending',
    'APPROVED': 'status-approved',
    'REJECTED': 'status-rejected',
    'CONVERTED_TO_NPC': 'status-converted'
  }
  return classes[status] || 'status-draft'
}

function formatCharacterStatus(status) {
  const labels = {
    'DRAFT': 'Draft',
    'PENDING_APPROVAL': 'Pending Approval',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected',
    'CONVERTED_TO_NPC': 'Converted to NPC'
  }
  return labels[status] || status
}

function getCharacterStatusBanner(character) {
  const status = character.status

  if (status === 'PENDING_APPROVAL') {
    return `
      <div class="character-status-banner banner-pending">
        <div class="banner-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </div>
        <div class="banner-content">
          <span class="banner-title">Awaiting Approval</span>
          <span class="banner-text">Your character has been submitted and is being reviewed by the Dungeon Master.</span>
        </div>
      </div>
    `
  }

  if (status === 'REJECTED') {
    return `
      <div class="character-status-banner banner-rejected">
        <div class="banner-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <div class="banner-content">
          <span class="banner-title">Changes Requested</span>
          <span class="banner-text">The DM has requested changes to your character. Please review the feedback and edit your character.</span>
          ${character.dm_feedback ? `
            <div class="banner-feedback">
              <strong>DM Feedback:</strong> ${escapeHtml(character.dm_feedback)}
            </div>
          ` : ''}
        </div>
      </div>
    `
  }

  if (status === 'DRAFT') {
    return `
      <div class="character-status-banner banner-draft">
        <div class="banner-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </div>
        <div class="banner-content">
          <span class="banner-title">Draft Character</span>
          <span class="banner-text">Your character is saved as a draft. Edit and submit it for DM approval when ready.</span>
        </div>
      </div>
    `
  }

  if (status === 'APPROVED') {
    return `
      <div class="character-status-banner banner-approved">
        <div class="banner-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
        </div>
        <div class="banner-content">
          <span class="banner-title">Character Approved</span>
          <span class="banner-text">Your character is ready to play!</span>
        </div>
      </div>
    `
  }

  return ''
}

// ========================================
// Pending Characters (DM)
// ========================================

let pendingCharacters = []

async function loadPendingCharacters(gameId) {
  console.log('[Game] Loading pending characters for game:', gameId)
  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/characters/pending`)
    
    if (!response.ok) {
      console.log('[Game] No pending characters or error:', response.status)
      return
    }

    pendingCharacters = await response.json()
    console.log('[Game] Pending characters loaded:', pendingCharacters.length, pendingCharacters)
    renderPendingCharacters(pendingCharacters)
  } catch (error) {
    console.error('[Game] Failed to load pending characters:', error)
  }
}

function renderPendingCharacters(characters) {
  const card = document.getElementById('pending-characters-card')
  const badge = document.getElementById('pending-count-badge')
  const list = document.getElementById('pending-characters-list')

  if (!card || !badge || !list) return

  if (characters.length === 0) {
    card.hidden = true
    return
  }

  card.hidden = false
  badge.textContent = characters.length

  list.innerHTML = characters.map(char => `
    <div class="pending-character-item" data-character-id="${char.id}">
      <div class="pending-character-info">
        <div class="pending-character-avatar">
          <span>${getInitials(char.name)}</span>
        </div>
        <div class="pending-character-details">
          <span class="pending-character-name">${escapeHtml(char.name)}</span>
          <span class="pending-character-meta">
            ${escapeHtml(char.data?.race || 'Unknown')} ${escapeHtml(char.data?.class || 'Unknown')}
          </span>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm btn-review" data-character-id="${char.id}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
        Review
      </button>
    </div>
  `).join('')

  setupPendingCharacterButtons()
}

function setupPendingCharacterButtons() {
  const reviewButtons = document.querySelectorAll('.btn-review')
  
  reviewButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation()
      const characterId = parseInt(btn.dataset.characterId)
      openCharacterReviewModal(characterId)
    })
  })
}

function openCharacterReviewModal(characterId) {
  const character = pendingCharacters.find(c => c.id === characterId)
  if (!character) return

  const existingModal = document.getElementById('character-review-modal')
  if (existingModal) existingModal.remove()

  const charData = character.data || {}
  const stats = charData.abilities || {}
  const hp = charData.hp || (10 + Math.floor(((stats.CON || 10) - 10) / 2))
  const ac = charData.ac || 10

  const modalHtml = `
    <div id="character-review-modal" class="modal-overlay">
      <div class="modal character-review-modal">
        <div class="modal-header">
          <h2>Review Character</h2>
          <button class="modal-close" id="close-review-modal">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="modal-body review-modal-scrollable">
          <div class="review-character-header">
            <div class="review-character-avatar">
              <span>${getInitials(character.name)}</span>
            </div>
            <div class="review-character-title">
              <h3>${escapeHtml(character.name)}</h3>
              <span class="review-character-subtitle">
                Level ${charData.level || 1} ${escapeHtml(charData.race || 'Unknown')} ${escapeHtml(charData.class || 'Unknown')}
              </span>
            </div>
          </div>

          <div class="review-combat-stats">
            <div class="review-combat-stat">
              <div class="combat-stat-icon hp-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
              </div>
              <div class="combat-stat-info">
                <span class="combat-stat-value">${hp}</span>
                <span class="combat-stat-label">Hit Points</span>
              </div>
            </div>
            <div class="review-combat-stat">
              <div class="combat-stat-icon ac-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/>
                </svg>
              </div>
              <div class="combat-stat-info">
                <span class="combat-stat-value">${ac}</span>
                <span class="combat-stat-label">Armor Class</span>
              </div>
            </div>
          </div>

          <div class="review-section">
            <h4>Ability Scores</h4>
            <div class="review-stats-grid">
              ${['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'].map(stat => `
                <div class="review-stat">
                  <span class="review-stat-label">${stat}</span>
                  <span class="review-stat-value">${stats[stat] || 10}</span>
                  <span class="review-stat-mod">${getModifier(stats[stat] || 10)}</span>
                </div>
              `).join('')}
            </div>
          </div>

          ${charData.background ? `
            <div class="review-section">
              <h4>Background</h4>
              <div class="review-info-box">${escapeHtml(charData.background)}</div>
            </div>
          ` : ''}

          ${charData.skills && charData.skills.length > 0 ? `
            <div class="review-section">
              <h4>Skill Proficiencies</h4>
              <div class="review-skills">
                ${charData.skills.map(skill => `<span class="review-skill-tag">${escapeHtml(skill)}</span>`).join('')}
              </div>
            </div>
          ` : ''}

          ${charData.description ? `
            <div class="review-section">
              <h4>Character Description</h4>
              <div class="review-description-box">${escapeHtml(charData.description)}</div>
            </div>
          ` : ''}

          <div class="review-section review-metadata">
            <h4>Submission Info</h4>
            <div class="review-meta-grid">
              <div class="review-meta-item">
                <span class="review-meta-label">Submitted</span>
                <span class="review-meta-value">${character.created_at ? new Date(character.created_at).toLocaleDateString() : 'Unknown'}</span>
              </div>
              <div class="review-meta-item">
                <span class="review-meta-label">Character ID</span>
                <span class="review-meta-value">#${character.id}</span>
              </div>
            </div>
          </div>

          <div class="review-section review-feedback-section" id="feedback-section" hidden>
            <h4>Feedback for Player</h4>
            <textarea 
              id="review-feedback" 
              class="review-feedback-input" 
              placeholder="Explain what needs to be changed..."
              rows="3"
            ></textarea>
          </div>
        </div>

        <div class="modal-footer review-actions">
          <button class="btn btn-ghost" id="btn-cancel-review">Cancel</button>
          <button class="btn btn-outline btn-warning" id="btn-request-changes">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Request Changes
          </button>
          <button class="btn btn-primary" id="btn-approve-character">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Approve
          </button>
        </div>
      </div>
    </div>
  `

  document.body.insertAdjacentHTML('beforeend', modalHtml)

  setupReviewModalHandlers(characterId)
}

function getModifier(score) {
  const mod = Math.floor((score - 10) / 2)
  return mod >= 0 ? `+${mod}` : `${mod}`
}

function setupReviewModalHandlers(characterId) {
  const modal = document.getElementById('character-review-modal')
  const closeBtn = document.getElementById('close-review-modal')
  const cancelBtn = document.getElementById('btn-cancel-review')
  const requestChangesBtn = document.getElementById('btn-request-changes')
  const approveBtn = document.getElementById('btn-approve-character')
  const feedbackSection = document.getElementById('feedback-section')
  const feedbackInput = document.getElementById('review-feedback')

  let isRequestingChanges = false

  const closeModal = () => {
    modal.remove()
  }

  closeBtn.addEventListener('click', closeModal)
  cancelBtn.addEventListener('click', closeModal)

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal()
  })

  requestChangesBtn.addEventListener('click', async () => {
    if (!isRequestingChanges) {
      isRequestingChanges = true
      feedbackSection.hidden = false
      feedbackInput.focus()
      requestChangesBtn.textContent = 'Submit Rejection'
      requestChangesBtn.classList.add('btn-danger')
      requestChangesBtn.classList.remove('btn-warning')
      return
    }

    const feedback = feedbackInput.value.trim()
    if (!feedback) {
      showMessage('Please provide feedback for the player', 'error')
      return
    }

    await rejectCharacter(characterId, feedback)
    closeModal()
  })

  approveBtn.addEventListener('click', async () => {
    await approveCharacter(characterId)
    closeModal()
  })
}

async function approveCharacter(characterId) {
  try {
    const response = await fetchWithAuth(`/api/v1/game/${currentGame.id}/character/${characterId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to approve character')
    }

    showMessage('Character approved!', 'success')
    pendingCharacters = pendingCharacters.filter(c => c.id !== characterId)
    renderPendingCharacters(pendingCharacters)
    await loadPlayers(currentGame.id)
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

async function rejectCharacter(characterId, feedback) {
  try {
    const response = await fetchWithAuth(`/api/v1/game/${currentGame.id}/character/${characterId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to reject character')
    }

    showMessage('Character returned for changes', 'success')
    pendingCharacters = pendingCharacters.filter(c => c.id !== characterId)
    renderPendingCharacters(pendingCharacters)
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

function addPendingCharacter(characterData) {
  pendingCharacters.push(characterData)
  renderPendingCharacters(pendingCharacters)
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

