/**
 * DM character approval/rejection management
 */
import { fetchWithAuth, escapeHtml, getInitials } from '../../utils/index.js'
import { gameState } from './game-state.js'

/**
 * Load pending characters waiting for DM approval
 */
export async function loadPendingCharacters(gameId) {
  console.log('[Game] Loading pending characters for game:', gameId)
  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/characters/pending`)
    
    if (!response.ok) {
      console.log('[Game] No pending characters or error:', response.status)
      return
    }

    gameState.pendingCharacters = await response.json()
    console.log('[Game] Pending characters loaded:', gameState.pendingCharacters.length, gameState.pendingCharacters)
    renderPendingCharacters(gameState.pendingCharacters)
  } catch (error) {
    console.error('[Game] Failed to load pending characters:', error)
  }
}

/**
 * Render the list of pending characters
 */
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

/**
 * Setup review buttons for pending characters
 */
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

/**
 * Open the character review modal
 */
function openCharacterReviewModal(characterId) {
  const character = gameState.pendingCharacters.find(c => c.id === characterId)
  if (!character) return

  const existingModal = document.getElementById('character-review-modal')
  if (existingModal) existingModal.remove()

  const charData = character.data || {}
  const stats = charData.abilities || {}

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

  // We need to pass callbacks from the caller
  // Using window events to communicate
  setupReviewModalHandlers(characterId, 
    (msg, type) => {
      window.dispatchEvent(new CustomEvent('game:message', { detail: { message: msg, type } }))
    },
    () => {
      window.dispatchEvent(new CustomEvent('game:reload-players'))
    }
  )
}

/**
 * Calculate ability score modifier
 */
function getModifier(score) {
  const mod = Math.floor((score - 10) / 2)
  return mod >= 0 ? `+${mod}` : `${mod}`
}

/**
 * Setup handlers for the review modal
 */
function setupReviewModalHandlers(characterId, onMessage, onPlayersReload) {
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
      if (onMessage) onMessage('Please provide feedback for the player', 'error')
      return
    }

    await rejectCharacter(characterId, feedback, onMessage)
    closeModal()
  })

  approveBtn.addEventListener('click', async () => {
    await approveCharacter(characterId, onMessage, onPlayersReload)
    closeModal()
  })
}

/**
 * Approve a pending character
 */
async function approveCharacter(characterId, onMessage, onPlayersReload) {
  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameState.currentGame.id}/character/${characterId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to approve character')
    }

    if (onMessage) onMessage('Character approved!', 'success')
    gameState.pendingCharacters = gameState.pendingCharacters.filter(c => c.id !== characterId)
    renderPendingCharacters(gameState.pendingCharacters)
    if (onPlayersReload) await onPlayersReload()
  } catch (error) {
    if (onMessage) onMessage(error.message, 'error')
  }
}

/**
 * Reject a character and request changes
 */
async function rejectCharacter(characterId, feedback, onMessage) {
  try {
    const response = await fetchWithAuth(`/api/v1/game/${gameState.currentGame.id}/character/${characterId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to reject character')
    }

    if (onMessage) onMessage('Character returned for changes', 'success')
    gameState.pendingCharacters = gameState.pendingCharacters.filter(c => c.id !== characterId)
    renderPendingCharacters(gameState.pendingCharacters)
  } catch (error) {
    if (onMessage) onMessage(error.message, 'error')
  }
}

/**
 * Add a new pending character to the list
 */
export function addPendingCharacter(characterData, onMessage) {
  gameState.pendingCharacters.push(characterData)
  renderPendingCharacters(gameState.pendingCharacters)
  if (onMessage) {
    onMessage(`New character "${characterData.name}" submitted by ${characterData.player_name}`, 'info')
  }
}

/**
 * Setup listener for new character submissions
 */
export function setupCharacterSubmissionListener(onMessage) {
  window.addEventListener('character:submitted', (event) => {
    const data = event.detail
    addPendingCharacter({
      id: data.character_id,
      name: data.character_name,
      user_id: data.user_id,
      game_id: data.game_id,
      data: {}
    }, onMessage)
  })
}
