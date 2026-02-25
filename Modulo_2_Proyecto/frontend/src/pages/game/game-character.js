/**
 * Player character management
 */
import { CharacterCreator, CharacterSheet } from '../../components/index.js'
import { navigate } from '../../router.js'
import { fetchWithAuth, escapeHtml, getInitials } from '../../utils/index.js'
import { gameState } from './game-state.js'

/**
 * Load the current user's character for this game
 */
export async function loadUserCharacter(gameId) {
  // Only load character for players, not DMs
  if (gameState.currentUserRole === 'DM') {
    return
  }

  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/my-character`)
    
    if (response.ok) {
      const character = await response.json()
      gameState.currentCharacter = character
      console.log('[Game] Character loaded:', character.name, 'Status:', character.status)
      renderCharacterSection(character)
    } else if (response.status === 404) {
      // No character exists, show create prompt
      gameState.currentCharacter = null
      renderNoCharacterSection()
    }
  } catch (error) {
    console.error('[Game] Failed to load character:', error)
    renderNoCharacterSection()
  }
}

/**
 * Render the character section when a character exists
 */
export function renderCharacterSection(character) {
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
          <button id="view-inventory-btn" class="btn btn-ghost btn-sm" type="button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 7h-9a2 2 0 0 1-2-2V2"></path>
              <path d="M9 2v3a2 2 0 0 0 2 2h9"></path>
              <path d="M3 7v13a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7"></path>
            </svg>
            Inventory
          </button>
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
    editBtn.addEventListener('click', () => {
      openCharacterCreator((msg, type) => {
        window.dispatchEvent(new CustomEvent('game:message', { detail: { message: msg, type } }))
      })
    })
  }

  // Setup inventory button
  const inventoryBtn = document.getElementById('view-inventory-btn')
  if (inventoryBtn) {
    inventoryBtn.addEventListener('click', () => {
      navigate(`/game/${gameState.currentGame.id}/inventory`)
    })
  }

  // Setup view full sheet button
  const viewSheetBtn = document.getElementById('view-full-sheet-btn')
  if (viewSheetBtn) {
    viewSheetBtn.addEventListener('click', () => {
      showCharacterSheet((msg, type) => {
        window.dispatchEvent(new CustomEvent('game:message', { detail: { message: msg, type } }))
      })
    })
  }
}

/**
 * Render the no character section (prompt to create)
 */
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
    createBtn.addEventListener('click', () => {
      openCharacterCreator((msg, type) => {
        window.dispatchEvent(new CustomEvent('game:message', { detail: { message: msg, type } }))
      })
    })
  }
}

/**
 * Open the character creator modal
 */
function openCharacterCreator(onMessage) {
  if (gameState.characterCreator) {
    gameState.characterCreator.destroy()
  }

  const rules = gameState.currentGame?.custom_rules || gameState.currentGame?.ruleset_template?.base_rules || {}
  const isEditing = gameState.currentCharacter && gameState.currentCharacter.id

  gameState.characterCreator = new CharacterCreator({
    gameId: gameState.currentGame.id,
    characterId: isEditing ? gameState.currentCharacter.id : null,
    rules: rules,
    onSubmit: (character) => {
      const message = isEditing ? 'Character updated and submitted!' : 'Character submitted for approval!'
      if (onMessage) onMessage(message, 'success')
      gameState.currentCharacter = character
      renderCharacterSection(character)
    },
    onSaveDraft: (character) => {
      const message = isEditing ? 'Character draft updated' : 'Character saved as draft'
      if (onMessage) onMessage(message, 'success')
      gameState.currentCharacter = character
      renderCharacterSection(character)
    },
    onCancel: () => {
      // Nothing special needed
    }
  })

  // If editing existing character, pre-populate the data
  if (isEditing) {
    gameState.characterCreator.characterData = {
      name: gameState.currentCharacter.name || '',
      race: gameState.currentCharacter.data?.race || '',
      class: gameState.currentCharacter.data?.class || '',
      level: gameState.currentCharacter.data?.level || 1,
      background: gameState.currentCharacter.data?.background || '',
      stats: gameState.currentCharacter.data?.abilities || {
        STR: 10, DEX: 10, CON: 10, INT: 10, WIS: 10, CHA: 10
      },
      skills: gameState.currentCharacter.data?.skills || [],
      description: gameState.currentCharacter.data?.description || ''
    }
    gameState.characterCreator.recalculatePoints()
  }

  gameState.characterCreator.init()
}

/**
 * Show the full character sheet modal
 */
function showCharacterSheet(onMessage) {
  if (gameState.characterSheet) {
    gameState.characterSheet.destroy()
  }

  if (!gameState.currentCharacter) {
    if (onMessage) onMessage('No character to display', 'error')
    return
  }

  // Only allow editing for APPROVED characters
  const isEditable = gameState.currentCharacter.status === 'APPROVED'

  gameState.characterSheet = new CharacterSheet({
    gameId: gameState.currentGame.id,
    characterId: gameState.currentCharacter.id,
    isEditable: isEditable,
    onUpdate: (character) => {
      gameState.currentCharacter = character
      renderCharacterSection(character)
      if (onMessage) onMessage('Character updated successfully', 'success')
    },
    onClose: () => {
      gameState.characterSheet = null
    }
  })

  gameState.characterSheet.init()
}

/**
 * Register character-related socket event listeners
 */
export function registerCharacterEventListeners() {
  if (!gameState.gameChat?.socketClient) {
    console.warn('[Game] Cannot register character events: no socket client')
    return
  }

  const socket = gameState.gameChat.socketClient

  // Listen for new character submissions (DM only)
  socket.on('character:submitted', (data) => {
    console.log('[Game] Character submitted event received:', data)
    if (gameState.currentUserRole === 'DM') {
      console.log('[Game] User is DM, showing submission message')
      // This will be handled by the game-dm-characters module
      // Dispatch a custom event for it to handle
      window.dispatchEvent(new CustomEvent('character:submitted', { detail: data }))
    } else {
      console.log('[Game] User is not DM, ignoring submission event')
    }
  })

  // Listen for character approval (Player)
  socket.on('character:approved', (data) => {
    console.log('[Game] Character approved event received:', data)
    console.log('[Game] currentUser:', gameState.currentUser)
    console.log('[Game] currentCharacter:', gameState.currentCharacter)
    console.log('[Game] Comparing user_id:', data.user_id, 'with currentUser.sub:', gameState.currentUser?.sub)

    if (gameState.currentUser && String(data.user_id) === String(gameState.currentUser.sub)) {
      console.log('[Game] User ID matched! Updating UI...')
      // This will be handled by a message callback
      window.dispatchEvent(new CustomEvent('character:approved', { 
        detail: { 
          message: 'Your character has been approved! You can now fully participate.',
          character_id: data.character_id,
          feedback: data.feedback
        }
      }))
      
      if (gameState.currentCharacter && gameState.currentCharacter.id === data.character_id) {
        console.log('[Game] Updating existing character status to APPROVED')
        gameState.currentCharacter.status = 'APPROVED'
        gameState.currentCharacter.dm_feedback = data.feedback
        renderCharacterSection(gameState.currentCharacter)
      } else {
        // Reload character if we don't have it or ID doesn't match
        console.log('[Game] Reloading character from server...')
        loadUserCharacter(gameState.currentGame.id)
      }
    } else {
      console.log('[Game] User ID did not match, ignoring approval event')
    }
  })

  // Listen for character rejection (Player)
  socket.on('character:rejected', (data) => {
    console.log('[Game] Character rejected event received:', data)
    console.log('[Game] currentUser:', gameState.currentUser)

    if (gameState.currentUser && String(data.user_id) === String(gameState.currentUser.sub)) {
      console.log('[Game] User ID matched! Showing rejection...')
      window.dispatchEvent(new CustomEvent('character:rejected', { 
        detail: { 
          message: 'The DM has requested changes to your character.',
          character_id: data.character_id,
          feedback: data.feedback
        }
      }))
      
      if (gameState.currentCharacter && gameState.currentCharacter.id === data.character_id) {
        console.log('[Game] Updating existing character status to REJECTED')
        gameState.currentCharacter.status = 'REJECTED'
        gameState.currentCharacter.dm_feedback = data.feedback
        renderCharacterSection(gameState.currentCharacter)
      } else {
        // Reload character if we don't have it
        console.log('[Game] Reloading character from server...')
        loadUserCharacter(gameState.currentGame.id)
      }
    } else {
      console.log('[Game] User ID did not match, ignoring rejection event')
    }
  })

  console.log('[Game] Character event listeners registered on socket:', socket)
}

// ========================================
// Helper Functions
// ========================================

function getCharacterStatusClass(status) {
  const classes = {
    'DRAFT': 'status-draft',
    'PENDING_APPROVAL': 'status-pending',
    'APPROVED': 'status-approved',
    'REJECTED': 'status-rejected'
  }
  return classes[status] || 'status-draft'
}

function formatCharacterStatus(status) {
  const labels = {
    'DRAFT': 'Draft',
    'PENDING_APPROVAL': 'Pending Approval',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected'
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
