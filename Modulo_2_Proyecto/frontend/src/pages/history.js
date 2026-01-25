import template from './history.html?raw'
import { fetchWithAuth, escapeHtml } from '../utils/index.js'
import { getRouteParams, navigate } from '../router.js'
import { Footer } from '../components/index.js'

export async function historyPage(app) {
  const { id: gameId } = getRouteParams()
  
  if (!gameId) {
    navigate('/dashboard')
    return
  }

  app.innerHTML = template + Footer()
  
  document.getElementById('back-to-game').href = `/game/${gameId}`
  
  await loadGameHistory(gameId)
  setupPrintButton()
}

async function loadGameHistory(gameId) {
  const loadingEl = document.getElementById('history-loading')
  const errorEl = document.getElementById('history-error')
  const logEl = document.getElementById('history-log')
  const emptyEl = document.getElementById('history-empty')
  const titleEl = document.getElementById('history-game-name')

  try {
    // Load game info first for the title
    const gameResponse = await fetchWithAuth(`/api/v1/game/${gameId}`)
    if (gameResponse.ok) {
      const game = await gameResponse.json()
      titleEl.textContent = `${game.name} - Adventure Log`
    }

    // Load all messages
    const response = await fetchWithAuth(`/api/v1/game/${gameId}/messages?limit=1000`)
    
    if (!response.ok) {
      throw new Error('Failed to load history')
    }

    const messages = await response.json()
    loadingEl.hidden = true

    if (messages.length === 0) {
      emptyEl.hidden = false
    } else {
      logEl.hidden = false
      renderHistoryLog(messages)
    }

  } catch (error) {
    console.error('[History] Error:', error)
    loadingEl.hidden = true
    errorEl.hidden = false
    document.getElementById('history-error-message').textContent = error.message
  }
}

function renderHistoryLog(messages) {
  const logEl = document.getElementById('history-log')
  
  // Group by date
  let lastDate = null
  
  messages.forEach(msg => {
    const date = new Date(msg.created_at)
    const dateStr = date.toLocaleDateString(undefined, { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
    
    if (dateStr !== lastDate) {
      const dateHeader = document.createElement('div')
      dateHeader.className = 'history-date-header'
      dateHeader.textContent = dateStr
      logEl.appendChild(dateHeader)
      lastDate = dateStr
    }
    
    const entryEl = document.createElement('div')
    entryEl.className = `history-entry type-${msg.message_type} ${msg.is_dm ? 'is-dm' : ''}`
    
    const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const displayName = msg.character_name || msg.username || msg.name || 'Unknown'
    
    if (msg.message_type === 'system') {
      entryEl.innerHTML = `
        <span class="entry-time">[${time}]</span>
        <span class="entry-system-text">${escapeHtml(msg.content)}</span>
      `
    } else if (msg.message_type === 'dice') {
      entryEl.innerHTML = `
        <span class="entry-time">[${time}]</span>
        <span class="entry-name">${escapeHtml(displayName)}:</span>
        <span class="entry-dice-text">${escapeHtml(msg.content)}</span>
      `
    } else {
      entryEl.innerHTML = `
        <span class="entry-time">[${time}]</span>
        <span class="entry-name">${escapeHtml(displayName)}${msg.is_dm ? ' (DM)' : ''}:</span>
        <span class="entry-text">${escapeHtml(msg.content)}</span>
      `
    }
    
    logEl.appendChild(entryEl)
  })
}

function setupPrintButton() {
  const printBtn = document.getElementById('print-history-btn')
  printBtn.addEventListener('click', () => {
    window.print()
  })
}
