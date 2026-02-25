import { navigate, getRouteParams } from '../router.js'
import { fetchWithAuth } from '../utils/index.js'
import { CharacterCreator } from '../components/index.js'

let characterCreator = null

export function joinPage(app) {
  app.innerHTML = getJoinTemplate()
  joinGameByCode()
}

function getJoinTemplate() {
  return `
    <div class="join-container">
      <div class="join-decoration">
        <div class="decoration-orb decoration-orb-1"></div>
        <div class="decoration-orb decoration-orb-2"></div>
        <div class="decoration-orb decoration-orb-3"></div>
      </div>
      <div class="join-card">
        <div class="join-loading" id="join-loading">
          <div class="join-spinner"></div>
          <p class="join-status" id="join-status">Joining game...</p>
        </div>
        <div class="join-error" id="join-error" hidden>
          <div class="join-error-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
          </div>
          <h3 class="join-error-title">Unable to Join</h3>
          <p class="join-error-message" id="join-error-message"></p>
          <button class="btn btn-primary" data-link href="/dashboard">Go to Dashboard</button>
        </div>
        <div class="join-success" id="join-success" hidden>
          <div class="join-success-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h3 class="join-success-title" id="join-game-name">Joined Successfully!</h3>
          <p class="join-success-message">Now let's create your character</p>
        </div>
      </div>
    </div>
  `
}

async function joinGameByCode() {
  const { code } = getRouteParams()
  
  try {
    updateStatus('Joining game...')
    const gameData = await performJoin(code)
    
    updateStatus('Checking character...')
    const hasCharacter = await checkIfHasCharacter(gameData.id)
    
    if (hasCharacter) {
      navigate(`/game/${gameData.id}`)
      return
    }
    
    updateStatus('Loading character creator...')
    const rules = await fetchGameRules(gameData.id)
    
    showSuccessState(gameData.name)
    openCharacterCreator(gameData.id, rules)
    
  } catch (error) {
    showError(error.message)
  }
}

async function performJoin(inviteCode) {
  const response = await fetchWithAuth('/api/v1/game/join-by-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ invite_code: inviteCode })
  })
  
  const data = await response.json()
  
  if (!response.ok) {
    throw new Error(data.detail || data.message || 'Failed to join game')
  }
  
  return data
}

async function checkIfHasCharacter(gameId) {
  const response = await fetchWithAuth(`/api/v1/game/${gameId}/my-character`)
  return response.ok
}

async function fetchGameRules(gameId) {
  const response = await fetchWithAuth(`/api/v1/game/${gameId}/rules`)
  
  if (!response.ok) {
    return {}
  }
  
  const data = await response.json()
  return data.effective_rules || {}
}

function openCharacterCreator(gameId, rules) {
  if (characterCreator) {
    characterCreator.destroy()
  }
  
  characterCreator = new CharacterCreator({
    gameId,
    rules,
    onSubmit: () => {
      navigateToGame(gameId)
    },
    onSaveDraft: () => {
      navigateToGame(gameId)
    },
    onCancel: () => {
      navigateToGame(gameId)
    }
  })
  
  characterCreator.init()
}

function navigateToGame(gameId) {
  if (characterCreator) {
    characterCreator.destroy()
    characterCreator = null
  }
  navigate(`/game/${gameId}`)
}

function updateStatus(message) {
  const statusEl = document.getElementById('join-status')
  if (statusEl) {
    statusEl.textContent = message
  }
}

function showSuccessState(gameName) {
  const loadingEl = document.getElementById('join-loading')
  const successEl = document.getElementById('join-success')
  const gameNameEl = document.getElementById('join-game-name')
  
  if (loadingEl) loadingEl.hidden = true
  if (successEl) successEl.hidden = false
  if (gameNameEl) gameNameEl.textContent = `Joined "${gameName}"!`
}

function showError(message) {
  const loadingEl = document.getElementById('join-loading')
  const errorEl = document.getElementById('join-error')
  const errorMessageEl = document.getElementById('join-error-message')
  
  if (loadingEl) loadingEl.hidden = true
  if (errorEl) errorEl.hidden = false
  if (errorMessageEl) errorMessageEl.textContent = message
}
