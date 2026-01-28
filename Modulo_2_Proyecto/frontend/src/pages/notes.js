import template from './notes.html?raw'
import { fetchWithAuth, escapeHtml } from '../utils/index.js'
import { getRouteParams, navigate } from '../router.js'
import { Footer } from '../components/index.js'

let currentGameId = null
let isDM = false
let notesData = { shared: [], private: [] }

export async function notesPage(app) {
  const { id: gameId } = getRouteParams()
  currentGameId = gameId
  
  if (!gameId) {
    navigate('/dashboard')
    return
  }

  app.innerHTML = template + Footer()
  
  document.getElementById('back-to-game').href = `/game/${gameId}`
  
  await initNotes(gameId)
  setupEventListeners()
}

async function initNotes(gameId) {
  const loadingEl = document.getElementById('notes-loading')
  const errorEl = document.getElementById('notes-error')
  const sectionsEl = document.getElementById('notes-sections')
  const titleEl = document.getElementById('notes-game-name')

  try {
    // Load game info to check if user is DM
    const gameResponse = await fetchWithAuth(`/api/v1/game/${gameId}`)
    if (!gameResponse.ok) throw new Error('Failed to load game info')
    
    const game = await gameResponse.json()
    titleEl.textContent = `${game.name} - Game Notes`
    isDM = game.role_in_game === 'DM'

    // Show visibility toggle only for DM
    const visibilityGroup = document.getElementById('visibility-group')
    if (visibilityGroup) {
      visibilityGroup.hidden = !isDM
    }

    await loadNotes(gameId)
    
    loadingEl.hidden = true
    sectionsEl.hidden = false

  } catch (error) {
    console.error('[Notes] Error:', error)
    loadingEl.hidden = true
    errorEl.hidden = false
    document.getElementById('notes-error-message').textContent = error.message
  }
}

async function loadNotes(gameId) {
  const response = await fetchWithAuth(`/api/v1/notes/${gameId}/notes`)
  if (!response.ok) throw new Error('Failed to load notes')
  
  notesData = await response.json()
  renderNotes()
}

function renderNotes() {
  renderNoteList('shared-notes-list', 'shared-notes-empty', notesData.shared, false)
  renderNoteList('private-notes-list', 'private-notes-empty', notesData.private, true)
}

function renderNoteList(listId, emptyId, notes, isPrivate) {
  const listEl = document.getElementById(listId)
  const emptyEl = document.getElementById(emptyId)
  
  listEl.innerHTML = ''
  
  if (notes.length === 0) {
    emptyEl.hidden = false
    listEl.hidden = true
    return
  }

  emptyEl.hidden = true
  listEl.hidden = false

  notes.forEach(note => {
    const card = document.createElement('div')
    card.className = 'note-card'
    
    const date = new Date(note.updated_at).toLocaleDateString()
    
    // Only author can edit/delete. For now, we assume current user is author of private notes
    // and DM is author of shared notes (backend enforces this anyway)
    const canManage = isPrivate || isDM

    card.innerHTML = `
      <div class="note-card-header">
        <h3 class="note-card-title">${escapeHtml(note.title)}</h3>
        <span class="note-card-date">${date}</span>
      </div>
      <div class="note-card-content">${escapeHtml(note.content).replace(/\n/g, '<br>')}</div>
      ${canManage ? `
        <div class="note-card-actions">
          <button class="btn btn-ghost btn-sm edit-note-btn" data-id="${note.id}" data-type="${isPrivate ? 'private' : 'shared'}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            Edit
          </button>
          <button class="btn btn-ghost btn-sm btn-danger delete-note-btn" data-id="${note.id}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            Delete
          </button>
        </div>
      ` : ''}
    `
    listEl.appendChild(card)
  })
}

function setupEventListeners() {
  const createBtn = document.getElementById('create-note-btn')
  const noteForm = document.getElementById('note-form')
  const noteModal = document.getElementById('note-modal')
  const deleteModal = document.getElementById('delete-modal')
  const confirmDeleteBtn = document.getElementById('confirm-delete-btn')
  
  // Open modal for new note
  createBtn.addEventListener('click', () => openModal())

  // Close modals
  document.querySelectorAll('.close-modal-btn, .cancel-modal-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      noteModal.hidden = true
      deleteModal.hidden = true
    })
  })

  // Handle form submission
  noteForm.addEventListener('submit', async (e) => {
    e.preventDefault()
    await saveNote()
  })

  // Delegate edit and delete buttons
  document.getElementById('notes-sections').addEventListener('click', (e) => {
    const editBtn = e.target.closest('.edit-note-btn')
    const deleteBtn = e.target.closest('.delete-note-btn')

    if (editBtn) {
      const noteId = editBtn.dataset.id
      const type = editBtn.dataset.type
      const note = notesData[type].find(n => n.id == noteId)
      openModal(note)
    }

    if (deleteBtn) {
      const noteId = deleteBtn.dataset.id
      openDeleteModal(noteId)
    }
  })

  // Confirm delete
  confirmDeleteBtn.addEventListener('click', async () => {
    const noteId = confirmDeleteBtn.dataset.id
    await deleteNote(noteId)
  })
}

function openModal(note = null) {
  const modal = document.getElementById('note-modal')
  const form = document.getElementById('note-form')
  const modalTitle = document.getElementById('modal-title-text')
  
  form.reset()
  
  if (note) {
    modalTitle.textContent = 'Edit Note'
    document.getElementById('note-id').value = note.id
    document.getElementById('note-title').value = note.title
    document.getElementById('note-content').value = note.content
    document.getElementById('note-visibility').checked = note.visibility === 'SHARED'
  } else {
    modalTitle.textContent = 'New Note'
    document.getElementById('note-id').value = ''
    document.getElementById('note-visibility').checked = false
  }
  
  modal.hidden = false
}

function openDeleteModal(noteId) {
  const modal = document.getElementById('delete-modal')
  document.getElementById('confirm-delete-btn').dataset.id = noteId
  modal.hidden = false
}

async function saveNote() {
  const noteId = document.getElementById('note-id').value
  const title = document.getElementById('note-title').value
  const content = document.getElementById('note-content').value
  const isShared = document.getElementById('note-visibility').checked
  
  const payload = {
    title,
    content,
    visibility: isShared ? 'SHARED' : 'PRIVATE'
  }

  try {
    let response
    if (noteId) {
      response = await fetchWithAuth(`/api/v1/notes/${currentGameId}/note/${noteId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      })
    } else {
      response = await fetchWithAuth(`/api/v1/notes/${currentGameId}/note`, {
        method: 'POST',
        body: JSON.stringify(payload)
      })
    }

    if (!response.ok) {
      let errorMessage = 'Failed to save note'
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorMessage
      } catch (e) {
        // If not JSON, use status text
        errorMessage = response.statusText || errorMessage
      }
      throw new Error(errorMessage)
    }

    document.getElementById('note-modal').hidden = true
    await loadNotes(currentGameId)

  } catch (error) {
    alert(error.message)
  }
}

async function deleteNote(noteId) {
  try {
    const response = await fetchWithAuth(`/api/v1/notes/${currentGameId}/note/${noteId}`, {
      method: 'DELETE'
    })

    if (!response.ok) {
      let errorMessage = 'Failed to delete note'
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorMessage
      } catch (e) {
        errorMessage = response.statusText || errorMessage
      }
      throw new Error(errorMessage)
    }

    document.getElementById('delete-modal').hidden = true
    await loadNotes(currentGameId)

  } catch (error) {
    alert(error.message)
  }
}
