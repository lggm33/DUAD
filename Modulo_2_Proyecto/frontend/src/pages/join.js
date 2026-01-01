import { navigate, getRouteParams } from '../router.js'
import { getAccessToken } from '../infrastructure/auth/auth.js'

export function joinPage(app) {
  app.innerHTML = `
    <div class="join-container">
      <div class="join-card">
        <div class="join-loading">
          <div class="spinner"></div>
          <p>Joining game...</p>
        </div>
        <div class="join-error" hidden>
          <p class="error-message"></p>
          <button class="btn btn-primary" data-link href="/dashboard">Go to Dashboard</button>
        </div>
      </div>
    </div>
  `

  joinGameByCode()
}

async function joinGameByCode() {
  const { code } = getRouteParams()
  const loadingEl = document.querySelector('.join-loading')
  const errorEl = document.querySelector('.join-error')
  const errorMessageEl = document.querySelector('.error-message')

  try {
    const response = await fetch('/api/v1/game/join-by-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAccessToken()}`
      },
      body: JSON.stringify({ invite_code: code })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to join game')
    }

    navigate(`/game/${data.id}`)
  } catch (error) {
    loadingEl.hidden = true
    errorEl.hidden = false
    errorMessageEl.textContent = error.message
  }
}

