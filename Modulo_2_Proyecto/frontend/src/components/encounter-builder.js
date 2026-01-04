/**
 * EncounterBuilder Component
 * 
 * Interface for DMs to create and configure encounters before activating them.
 * Supports drag-and-drop style adding of NPCs and Characters to encounters,
 * difficulty calculation, and encounter management.
 */

import { fetchWithAuth, escapeHtml, getInitials } from '../utils/index.js'

const MODAL_ID = 'encounter-builder-modal'

const DIFFICULTY_COLORS = {
  TRIVIAL: 'var(--color-text-muted)',
  EASY: 'var(--color-success)',
  MEDIUM: 'var(--color-warning)',
  HARD: 'var(--color-error)',
  DEADLY: '#dc2626'
}

const DIFFICULTY_OPTIONS = ['TRIVIAL', 'EASY', 'MEDIUM', 'HARD', 'DEADLY']

export class EncounterBuilder {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.gameId - The ID of the game
   * @param {number} [options.encounterId] - Optional encounter ID for editing
   * @param {Function} options.onSave - Callback when encounter is saved
   * @param {Function} options.onActivate - Callback when encounter is activated
   * @param {Function} options.onCancel - Callback when creation is cancelled
   */
  constructor(options) {
    this.gameId = options.gameId
    this.encounterId = options.encounterId || null
    this.onSave = options.onSave
    this.onActivate = options.onActivate
    this.onCancel = options.onCancel

    this.encounterData = {
      name: '',
      description: '',
      location: '',
      difficulty: null,
      estimated_xp: 0,
      notes: ''
    }

    this.availableNPCs = []
    this.availableCharacters = []
    this.selectedParticipants = []
    this.errors = []
    this.isLoading = false
    this.isSaving = false
    this.isEditing = Boolean(this.encounterId)
  }

  /**
   * Initialize and show the encounter builder modal
   */
  async init() {
    this.ensureModalExists()
    this.renderLoading()
    this.show()

    await this.loadData()
    this.renderForm()
    this.setupEventListeners()
  }

  /**
   * Load NPCs, Characters, and existing encounter data
   */
  async loadData() {
    this.isLoading = true

    try {
      const [npcsResponse, charactersResponse] = await Promise.all([
        fetchWithAuth(`/api/v1/game/${this.gameId}/npcs?active_only=true`),
        fetchWithAuth(`/api/v1/game/${this.gameId}/characters?status=APPROVED`)
      ])

      if (npcsResponse.ok) {
        this.availableNPCs = await npcsResponse.json()
      }

      if (charactersResponse.ok) {
        this.availableCharacters = await charactersResponse.json()
      }

      if (this.encounterId) {
        const encounterResponse = await fetchWithAuth(
          `/api/v1/game/${this.gameId}/encounter/${this.encounterId}`
        )
        if (encounterResponse.ok) {
          const encounter = await encounterResponse.json()
          this.encounterData = {
            name: encounter.name || '',
            description: encounter.description || '',
            location: encounter.location || '',
            difficulty: encounter.difficulty || null,
            estimated_xp: encounter.estimated_xp || 0,
            notes: encounter.notes || ''
          }
          this.selectedParticipants = this.parseParticipants(encounter.participants || [])
        }
      }
    } catch (error) {
      this.errors = [`Failed to load data: ${error.message}`]
    }

    this.isLoading = false
  }

  /**
   * Parse participants from API response
   */
  parseParticipants(participants) {
    return participants.map(p => ({
      id: p.id,
      type: p.participant_type,
      participantId: p.participant_id,
      instanceIndex: p.instance_index,
      name: p.name || this.getParticipantName(p),
      quantity: 1,
      notes: p.notes
    }))
  }

  /**
   * Get participant name from NPC or Character lists
   */
  getParticipantName(participant) {
    if (participant.participant_type === 'CHARACTER') {
      const char = this.availableCharacters.find(c => c.id === participant.participant_id)
      return char?.name || 'Unknown Character'
    } else {
      const npc = this.availableNPCs.find(n => n.id === participant.participant_id)
      const baseName = npc?.name || 'Unknown NPC'
      return participant.instance_index > 1 
        ? `${baseName} ${participant.instance_index}` 
        : baseName
    }
  }

  /**
   * Ensure the modal container exists in the DOM
   */
  ensureModalExists() {
    if (!document.getElementById(MODAL_ID)) {
      document.body.insertAdjacentHTML('beforeend', this.getModalTemplate())
    }
  }

  /**
   * Get the base modal HTML template
   */
  getModalTemplate() {
    return `
      <div id="${MODAL_ID}" class="eb-overlay" hidden>
        <div class="eb-modal">
          <div class="eb-header">
            <div class="eb-header-left">
              <div class="eb-header-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <path d="m10 13-2 2 2 2"></path>
                  <path d="m14 17 2-2-2-2"></path>
                </svg>
              </div>
              <h2 class="eb-title">${this.isEditing ? 'Edit Encounter' : 'Create Encounter'}</h2>
            </div>
            <button id="eb-close-btn" class="eb-close" type="button">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="eb-body" id="eb-form-container">
            <!-- Form content rendered dynamically -->
          </div>
          <div class="eb-footer">
            <div class="eb-footer-info">
              <span id="eb-participant-count" class="eb-participant-count">0 participants</span>
            </div>
            <div class="eb-footer-actions">
              <button id="eb-cancel-btn" class="btn eb-btn-cancel" type="button">
                Cancel
              </button>
              <button id="eb-save-btn" class="btn eb-btn-save" type="button">
                Save Draft
              </button>
              <button id="eb-activate-btn" class="btn eb-btn-activate" type="button">
                Activate Encounter
              </button>
            </div>
          </div>
        </div>
      </div>
    `
  }

  /**
   * Render loading state
   */
  renderLoading() {
    const container = document.getElementById('eb-form-container')
    if (!container) return

    container.innerHTML = `
      <div class="eb-loading">
        <span class="loader loader-lg"></span>
        <p>Loading encounter data...</p>
      </div>
    `
  }

  /**
   * Render the complete form content
   */
  renderForm() {
    const container = document.getElementById('eb-form-container')
    if (!container) return

    container.innerHTML = `
      ${this.renderValidationSummary()}
      ${this.renderBasicInfoSection()}
      ${this.renderParticipantsSection()}
      ${this.renderSummarySection()}
    `

    this.updateParticipantCount()
    this.updateDifficultyPreview()
  }

  /**
   * Render validation errors summary
   */
  renderValidationSummary() {
    if (this.errors.length === 0) return ''

    return `
      <div class="eb-validation-summary">
        <h4>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
          Please fix the following errors:
        </h4>
        <ul>
          ${this.errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')}
        </ul>
      </div>
    `
  }

  /**
   * Render the basic info section
   */
  renderBasicInfoSection() {
    return `
      <div class="eb-form-section">
        <div class="eb-section-header">
          <svg class="eb-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
          <h3 class="eb-section-title">Encounter Details</h3>
        </div>
        
        <div class="eb-form-grid">
          <div class="eb-form-group eb-form-full">
            <label class="eb-form-label eb-form-label-required" for="eb-name">Encounter Name</label>
            <input 
              type="text" 
              id="eb-name" 
              class="eb-form-input" 
              placeholder="e.g., Goblin Ambush, Dragon's Lair..."
              value="${escapeHtml(this.encounterData.name)}"
              maxlength="100"
              required
            />
          </div>
          
          <div class="eb-form-group">
            <label class="eb-form-label" for="eb-location">Location</label>
            <input 
              type="text" 
              id="eb-location" 
              class="eb-form-input" 
              placeholder="e.g., Dark Forest, Dungeon Level 2..."
              value="${escapeHtml(this.encounterData.location)}"
              maxlength="100"
            />
          </div>
          
          <div class="eb-form-group">
            <label class="eb-form-label" for="eb-difficulty">Difficulty</label>
            <select id="eb-difficulty" class="eb-form-select">
              <option value="">Auto-calculate</option>
              ${DIFFICULTY_OPTIONS.map(diff => `
                <option value="${diff}" ${this.encounterData.difficulty === diff ? 'selected' : ''}>
                  ${diff.charAt(0) + diff.slice(1).toLowerCase()}
                </option>
              `).join('')}
            </select>
          </div>
          
          <div class="eb-form-group eb-form-full">
            <label class="eb-form-label" for="eb-description">Description</label>
            <textarea 
              id="eb-description" 
              class="eb-form-textarea" 
              placeholder="Describe the encounter setup, environment, and objectives..."
              rows="2"
              maxlength="500"
            >${escapeHtml(this.encounterData.description)}</textarea>
          </div>
          
          <div class="eb-form-group eb-form-full">
            <label class="eb-form-label" for="eb-notes">DM Notes (private)</label>
            <textarea 
              id="eb-notes" 
              class="eb-form-textarea eb-notes-textarea" 
              placeholder="Tactics, secrets, loot distribution..."
              rows="2"
              maxlength="1000"
            >${escapeHtml(this.encounterData.notes)}</textarea>
            <span class="eb-form-hint">Only visible to you</span>
          </div>
        </div>
      </div>
    `
  }

  /**
   * Render the participants section with NPCs and Characters
   */
  renderParticipantsSection() {
    return `
      <div class="eb-form-section">
        <div class="eb-section-header">
          <svg class="eb-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <h3 class="eb-section-title">Participants</h3>
        </div>
        
        <div class="eb-participants-layout">
          <!-- Available Pool -->
          <div class="eb-pool-section">
            <div class="eb-pool-header">
              <h4 class="eb-pool-title">Available</h4>
            </div>
            
            <!-- NPCs -->
            <div class="eb-pool-category">
              <h5 class="eb-category-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="8.5" cy="7" r="4"></circle>
                  <path d="M20 8v6"></path>
                  <path d="M23 11h-6"></path>
                </svg>
                NPCs
              </h5>
              <div class="eb-pool-items" id="eb-npc-pool">
                ${this.renderNPCPool()}
              </div>
            </div>
            
            <!-- Characters -->
            <div class="eb-pool-category">
              <h5 class="eb-category-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                Party Characters
              </h5>
              <div class="eb-pool-items" id="eb-character-pool">
                ${this.renderCharacterPool()}
              </div>
            </div>
          </div>
          
          <!-- Selected Participants -->
          <div class="eb-encounter-section">
            <div class="eb-encounter-header">
              <h4 class="eb-encounter-title">In Encounter</h4>
            </div>
            <div class="eb-encounter-arena" id="eb-encounter-arena">
              ${this.renderSelectedParticipants()}
            </div>
          </div>
        </div>
      </div>
    `
  }

  /**
   * Render available NPCs pool
   */
  renderNPCPool() {
    if (this.availableNPCs.length === 0) {
      return '<div class="eb-pool-empty">No NPCs created yet</div>'
    }

    return this.availableNPCs.map(npc => {
      const stats = npc.stats || {}
      const hp = stats.hp || '?'
      const ac = stats.ac || '?'
      
      return `
        <div class="eb-pool-item eb-pool-item-npc" data-type="NPC" data-id="${npc.id}">
          <div class="eb-pool-item-avatar eb-avatar-npc">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
              <line x1="9" y1="9" x2="9.01" y2="9"></line>
              <line x1="15" y1="9" x2="15.01" y2="9"></line>
            </svg>
          </div>
          <div class="eb-pool-item-info">
            <span class="eb-pool-item-name">${escapeHtml(npc.name)}</span>
            <span class="eb-pool-item-stats">HP: ${hp} | AC: ${ac}</span>
          </div>
          <div class="eb-quantity-controls">
            <input 
              type="number" 
              class="eb-quantity-input" 
              value="1" 
              min="1" 
              max="20"
              data-npc-id="${npc.id}"
            />
          </div>
          <button class="eb-add-btn" data-type="NPC" data-id="${npc.id}" title="Add to encounter">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </button>
        </div>
      `
    }).join('')
  }

  /**
   * Render available Characters pool
   */
  renderCharacterPool() {
    if (this.availableCharacters.length === 0) {
      return '<div class="eb-pool-empty">No approved characters</div>'
    }

    return this.availableCharacters.map(char => {
      const data = char.data || {}
      const isInEncounter = this.selectedParticipants.some(
        p => p.type === 'CHARACTER' && p.participantId === char.id
      )
      
      return `
        <div class="eb-pool-item eb-pool-item-character ${isInEncounter ? 'eb-pool-item-disabled' : ''}" 
             data-type="CHARACTER" 
             data-id="${char.id}">
          <div class="eb-pool-item-avatar eb-avatar-character">
            ${getInitials(char.name)}
          </div>
          <div class="eb-pool-item-info">
            <span class="eb-pool-item-name">${escapeHtml(char.name)}</span>
            <span class="eb-pool-item-stats">${escapeHtml(data.race || '?')} ${escapeHtml(data.class || '?')}</span>
          </div>
          <button 
            class="eb-add-btn" 
            data-type="CHARACTER" 
            data-id="${char.id}"
            title="${isInEncounter ? 'Already in encounter' : 'Add to encounter'}"
            ${isInEncounter ? 'disabled' : ''}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              ${isInEncounter 
                ? '<polyline points="20 6 9 17 4 12"></polyline>'
                : '<line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>'
              }
            </svg>
          </button>
        </div>
      `
    }).join('')
  }

  /**
   * Render selected participants in encounter
   */
  renderSelectedParticipants() {
    if (this.selectedParticipants.length === 0) {
      return `
        <div class="eb-encounter-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <p>Add NPCs and Characters to this encounter</p>
        </div>
      `
    }

    return this.selectedParticipants.map((participant, index) => {
      const isNPC = participant.type === 'NPC'
      
      return `
        <div class="eb-participant-card ${isNPC ? 'eb-participant-npc' : 'eb-participant-character'}" 
             data-index="${index}">
          <div class="eb-participant-avatar ${isNPC ? 'eb-avatar-npc' : 'eb-avatar-character'}">
            ${isNPC 
              ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                </svg>`
              : getInitials(participant.name)
            }
          </div>
          <div class="eb-participant-info">
            <span class="eb-participant-name">${escapeHtml(participant.name)}</span>
            <span class="eb-participant-type">${isNPC ? 'NPC' : 'Player Character'}</span>
          </div>
          <button class="eb-remove-btn" data-index="${index}" title="Remove from encounter">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      `
    }).join('')
  }

  /**
   * Render the summary section
   */
  renderSummarySection() {
    const difficulty = this.encounterData.difficulty || 'MEDIUM'
    const difficultyColor = DIFFICULTY_COLORS[difficulty] || DIFFICULTY_COLORS.MEDIUM
    const participantCount = this.selectedParticipants.length
    const npcCount = this.selectedParticipants.filter(p => p.type === 'NPC').length
    const pcCount = this.selectedParticipants.filter(p => p.type === 'CHARACTER').length

    return `
      <div class="eb-form-section">
        <div class="eb-section-header">
          <svg class="eb-section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="3" y1="9" x2="21" y2="9"></line>
            <line x1="9" y1="21" x2="9" y2="9"></line>
          </svg>
          <h3 class="eb-section-title">Summary</h3>
        </div>
        
        <div class="eb-summary-grid">
          <div class="eb-summary-card">
            <div class="eb-summary-value" id="eb-summary-participants">${participantCount}</div>
            <div class="eb-summary-label">Participants</div>
            <div class="eb-summary-detail">${npcCount} NPCs, ${pcCount} PCs</div>
          </div>
          
          <div class="eb-summary-card">
            <div class="eb-summary-value eb-summary-difficulty" id="eb-summary-difficulty" style="color: ${difficultyColor}">
              ${difficulty}
            </div>
            <div class="eb-summary-label">Difficulty</div>
          </div>
          
          <div class="eb-summary-card">
            <div class="eb-summary-value" id="eb-summary-xp">${this.encounterData.estimated_xp || 0}</div>
            <div class="eb-summary-label">Estimated XP</div>
          </div>
        </div>
      </div>
    `
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    const modal = document.getElementById(MODAL_ID)
    if (!modal) return

    // Close button
    const closeBtn = document.getElementById('eb-close-btn')
    closeBtn?.addEventListener('click', () => this.handleCancel())

    // Cancel button
    const cancelBtn = document.getElementById('eb-cancel-btn')
    cancelBtn?.addEventListener('click', () => this.handleCancel())

    // Click outside to close
    modal.addEventListener('click', (e) => {
      if (e.target === modal) this.handleCancel()
    })

    // Escape key to close
    this.escapeHandler = (e) => {
      if (e.key === 'Escape' && !modal.hidden) {
        this.handleCancel()
      }
    }
    document.addEventListener('keydown', this.escapeHandler)

    // Form inputs
    this.setupFormInputListeners()

    // Participant buttons
    this.setupParticipantListeners()

    // Footer buttons
    document.getElementById('eb-save-btn')?.addEventListener('click', () => this.handleSave())
    document.getElementById('eb-activate-btn')?.addEventListener('click', () => this.handleActivate())
  }

  /**
   * Setup listeners for form input changes
   */
  setupFormInputListeners() {
    const nameInput = document.getElementById('eb-name')
    const locationInput = document.getElementById('eb-location')
    const difficultySelect = document.getElementById('eb-difficulty')
    const descriptionTextarea = document.getElementById('eb-description')
    const notesTextarea = document.getElementById('eb-notes')

    nameInput?.addEventListener('input', (e) => {
      this.encounterData.name = e.target.value
    })

    locationInput?.addEventListener('input', (e) => {
      this.encounterData.location = e.target.value
    })

    difficultySelect?.addEventListener('change', (e) => {
      this.encounterData.difficulty = e.target.value || null
      this.updateDifficultyPreview()
    })

    descriptionTextarea?.addEventListener('input', (e) => {
      this.encounterData.description = e.target.value
    })

    notesTextarea?.addEventListener('input', (e) => {
      this.encounterData.notes = e.target.value
    })
  }

  /**
   * Setup listeners for participant add/remove
   */
  setupParticipantListeners() {
    // Add buttons
    const addButtons = document.querySelectorAll('.eb-add-btn')
    addButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault()
        const type = btn.dataset.type
        const id = parseInt(btn.dataset.id)
        
        if (type === 'NPC') {
          const quantityInput = btn.closest('.eb-pool-item')?.querySelector('.eb-quantity-input')
          const quantity = parseInt(quantityInput?.value) || 1
          this.addNPCToEncounter(id, quantity)
        } else {
          this.addCharacterToEncounter(id)
        }
      })
    })

    // Remove buttons
    const removeButtons = document.querySelectorAll('.eb-remove-btn')
    removeButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault()
        const index = parseInt(btn.dataset.index)
        this.removeParticipant(index)
      })
    })
  }

  /**
   * Add NPC to encounter
   */
  addNPCToEncounter(npcId, quantity = 1) {
    const npc = this.availableNPCs.find(n => n.id === npcId)
    if (!npc) return

    // Find the current max instance index for this NPC
    const existingInstances = this.selectedParticipants.filter(
      p => p.type === 'NPC' && p.participantId === npcId
    )
    let startIndex = existingInstances.length > 0 
      ? Math.max(...existingInstances.map(p => p.instanceIndex)) + 1 
      : 1

    for (let i = 0; i < quantity; i++) {
      const instanceIndex = startIndex + i
      this.selectedParticipants.push({
        type: 'NPC',
        participantId: npcId,
        instanceIndex: instanceIndex,
        name: instanceIndex > 1 ? `${npc.name} ${instanceIndex}` : npc.name,
        quantity: 1
      })
    }

    this.refreshParticipantsUI()
  }

  /**
   * Add Character to encounter
   */
  addCharacterToEncounter(characterId) {
    // Check if already in encounter
    const exists = this.selectedParticipants.some(
      p => p.type === 'CHARACTER' && p.participantId === characterId
    )
    if (exists) return

    const char = this.availableCharacters.find(c => c.id === characterId)
    if (!char) return

    this.selectedParticipants.push({
      type: 'CHARACTER',
      participantId: characterId,
      instanceIndex: 1,
      name: char.name,
      quantity: 1
    })

    this.refreshParticipantsUI()
  }

  /**
   * Remove participant from encounter
   */
  removeParticipant(index) {
    this.selectedParticipants.splice(index, 1)
    this.refreshParticipantsUI()
  }

  /**
   * Refresh the participants UI after changes
   */
  refreshParticipantsUI() {
    const arena = document.getElementById('eb-encounter-arena')
    if (arena) {
      arena.innerHTML = this.renderSelectedParticipants()
    }

    const characterPool = document.getElementById('eb-character-pool')
    if (characterPool) {
      characterPool.innerHTML = this.renderCharacterPool()
    }

    this.setupParticipantListeners()
    this.updateParticipantCount()
    this.updateDifficultyPreview()
  }

  /**
   * Update participant count display
   */
  updateParticipantCount() {
    const countEl = document.getElementById('eb-participant-count')
    const summaryEl = document.getElementById('eb-summary-participants')
    const count = this.selectedParticipants.length
    const npcCount = this.selectedParticipants.filter(p => p.type === 'NPC').length
    const pcCount = this.selectedParticipants.filter(p => p.type === 'CHARACTER').length

    if (countEl) {
      countEl.textContent = `${count} participant${count !== 1 ? 's' : ''}`
    }

    if (summaryEl) {
      summaryEl.textContent = count
      const detailEl = summaryEl.parentElement?.querySelector('.eb-summary-detail')
      if (detailEl) {
        detailEl.textContent = `${npcCount} NPCs, ${pcCount} PCs`
      }
    }
  }

  /**
   * Update difficulty preview
   */
  updateDifficultyPreview() {
    const difficultyEl = document.getElementById('eb-summary-difficulty')
    if (!difficultyEl) return

    const difficulty = this.encounterData.difficulty || 'MEDIUM'
    const difficultyColor = DIFFICULTY_COLORS[difficulty] || DIFFICULTY_COLORS.MEDIUM

    difficultyEl.textContent = difficulty
    difficultyEl.style.color = difficultyColor
  }

  /**
   * Validate the encounter data
   */
  validate() {
    this.errors = []

    if (!this.encounterData.name.trim()) {
      this.errors.push('Encounter name is required')
    }

    return this.errors.length === 0
  }

  /**
   * Build the encounter data payload for API
   */
  buildPayload() {
    return {
      name: this.encounterData.name.trim(),
      description: this.encounterData.description || null,
      location: this.encounterData.location || null,
      difficulty: this.encounterData.difficulty || null,
      estimated_xp: this.encounterData.estimated_xp || null,
      notes: this.encounterData.notes || null
    }
  }

  /**
   * Handle save as draft
   */
  async handleSave() {
    if (this.isSaving) return

    if (!this.validate()) {
      this.renderForm()
      this.setupEventListeners()
      return
    }

    this.isSaving = true
    const saveBtn = document.getElementById('eb-save-btn')
    if (saveBtn) {
      saveBtn.disabled = true
      saveBtn.textContent = 'Saving...'
    }

    try {
      const payload = this.buildPayload()
      let encounterResponse

      if (this.encounterId) {
        encounterResponse = await fetchWithAuth(
          `/api/v1/game/${this.gameId}/encounter/${this.encounterId}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }
        )
      } else {
        encounterResponse = await fetchWithAuth(
          `/api/v1/game/${this.gameId}/encounter`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }
        )
      }

      if (!encounterResponse.ok) {
        const error = await encounterResponse.json()
        throw new Error(error.message || 'Failed to save encounter')
      }

      const encounter = await encounterResponse.json()
      this.encounterId = encounter.id

      // Save participants
      await this.saveParticipants()

      this.hide()
      if (this.onSave) {
        this.onSave(encounter)
      }
    } catch (error) {
      this.errors = [error.message]
      this.renderForm()
      this.setupEventListeners()
    } finally {
      this.isSaving = false
      if (saveBtn) {
        saveBtn.disabled = false
        saveBtn.textContent = 'Save Draft'
      }
    }
  }

  /**
   * Save participants to the encounter
   */
  async saveParticipants() {
    if (!this.encounterId) return

    // Group NPCs by participantId for bulk add
    const npcGroups = {}
    const characters = []

    for (const participant of this.selectedParticipants) {
      if (participant.type === 'NPC') {
        if (!npcGroups[participant.participantId]) {
          npcGroups[participant.participantId] = 0
        }
        npcGroups[participant.participantId]++
      } else {
        characters.push(participant.participantId)
      }
    }

    // Add NPCs
    for (const [npcId, quantity] of Object.entries(npcGroups)) {
      await fetchWithAuth(
        `/api/v1/game/${this.gameId}/encounter/${this.encounterId}/participants`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            participant_type: 'NPC',
            participant_id: parseInt(npcId),
            quantity: quantity
          })
        }
      )
    }

    // Add Characters
    for (const characterId of characters) {
      await fetchWithAuth(
        `/api/v1/game/${this.gameId}/encounter/${this.encounterId}/participants`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            participant_type: 'CHARACTER',
            participant_id: characterId
          })
        }
      )
    }
  }

  /**
   * Handle activate encounter
   */
  async handleActivate() {
    if (this.isSaving) return

    if (!this.validate()) {
      this.renderForm()
      this.setupEventListeners()
      return
    }

    if (this.selectedParticipants.length === 0) {
      this.errors = ['Add at least one participant before activating']
      this.renderForm()
      this.setupEventListeners()
      return
    }

    // First save, then activate
    await this.handleSave()

    // The onSave callback will handle closing the modal
    // The caller should handle activation logic
    if (this.onActivate && this.encounterId) {
      this.onActivate(this.encounterId)
    }
  }

  /**
   * Handle cancel action
   */
  handleCancel() {
    this.hide()
    if (this.onCancel) {
      this.onCancel()
    }
  }

  /**
   * Show the modal
   */
  show() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = false
      document.body.style.overflow = 'hidden'
    }
  }

  /**
   * Hide the modal
   */
  hide() {
    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.hidden = true
      document.body.style.overflow = ''
    }
  }

  /**
   * Destroy the modal and cleanup
   */
  destroy() {
    if (this.escapeHandler) {
      document.removeEventListener('keydown', this.escapeHandler)
    }

    const modal = document.getElementById(MODAL_ID)
    if (modal) {
      modal.remove()
    }
    document.body.style.overflow = ''
  }
}

