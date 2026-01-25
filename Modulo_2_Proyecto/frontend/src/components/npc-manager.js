/**
 * NPCManager Component
 * 
 * Panel exclusive for DM with complete CRUD operations for NPCs.
 * Allows creating, editing, deleting NPCs and converting them to player characters.
 */

import { fetchWithAuth, escapeHtml, getInitials } from '../utils/index.js'
import { DiceService } from '../utils/dice-service.js'

const MODAL_ID = 'npc-manager-modal'
const FORM_MODAL_ID = 'npc-form-modal'

const NPC_TYPES = {
  ALLY: { label: 'Ally', class: 'npc-type-ally', icon: '🤝' },
  ENEMY: { label: 'Enemy', class: 'npc-type-enemy', icon: '⚔️' },
  NEUTRAL: { label: 'Neutral', class: 'npc-type-neutral', icon: '🏪' },
  BOSS: { label: 'Boss', class: 'npc-type-boss', icon: '👹' },
  COMPANION: { label: 'Companion', class: 'npc-type-companion', icon: '🐺' }
}

const NPC_STATUSES = {
  ACTIVE: { label: 'Active', class: 'npc-status-active' },
  DEFEATED: { label: 'Defeated', class: 'npc-status-defeated' },
  RETIRED: { label: 'Retired', class: 'npc-status-retired' },
  CONVERTED_TO_PC: { label: 'Converted to PC', class: 'npc-status-converted' }
}

export class NPCManager {
  /**
   * @param {Object} options - Configuration options
   * @param {number} options.gameId - The ID of the game
   * @param {Object} options.socketClient - Socket client for real-time communication
   * @param {Function} options.onNPCCreated - Callback when NPC is created
   * @param {Function} options.onNPCUpdated - Callback when NPC is updated
   * @param {Function} options.onNPCDeleted - Callback when NPC is deleted
   * @param {Function} options.onError - Callback for error messages
   * @param {Function} options.onSuccess - Callback for success messages
   */
  constructor(options) {
    this.gameId = options.gameId
    this.socketClient = options.socketClient
    this.onNPCCreated = options.onNPCCreated
    this.onNPCUpdated = options.onNPCUpdated
    this.onNPCDeleted = options.onNPCDeleted
    this.onError = options.onError || console.error
    this.onSuccess = options.onSuccess || console.log

    this.npcs = []
    this.isLoading = true
    this.error = null
    this.editingNPC = null
    this.filterType = null
    this.filterStatus = 'ACTIVE'
  }

  /**
   * Initialize the NPC Manager
   */
  async init() {
    this.ensureContainerExists()
    await this.loadNPCs()
  }

  /**
   * Ensure the container exists in the DOM
   */
  ensureContainerExists() {
    const container = document.getElementById('npc-manager-container')
    if (!container) {
      console.warn('NPC Manager container not found in DOM')
    }
  }

  /**
   * Load NPCs from the API
   */
  async loadNPCs() {
    try {
      this.isLoading = true
      this.error = null
      this.render()

      let url = `/api/v1/game/${this.gameId}/npcs`
      const params = new URLSearchParams()
      
      if (this.filterStatus === 'ACTIVE') {
        params.append('active_only', 'true')
      }
      if (this.filterType) {
        params.append('npc_type', this.filterType)
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`
      }

      const response = await fetchWithAuth(url)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to load NPCs')
      }

      this.npcs = await response.json()
      this.isLoading = false
      this.render()
    } catch (error) {
      this.error = error.message
      this.isLoading = false
      this.render()
    }
  }

  /**
   * Render the NPC Manager section
   */
  render() {
    const container = document.getElementById('npc-manager-container')
    if (!container) return

    container.innerHTML = `
      <div class="npc-manager">
        ${this.renderHeader()}
        ${this.renderFilters()}
        ${this.renderContent()}
      </div>
    `

    this.setupEventListeners()
  }

  /**
   * Render the header with title and create button
   */
  renderHeader() {
    return `
      <div class="npc-manager-header">
        <div class="npc-manager-title">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <h3>NPC Management</h3>
          <span class="npc-count">${this.npcs.length} NPC${this.npcs.length !== 1 ? 's' : ''}</span>
        </div>
        <button id="create-npc-btn" class="btn btn-primary btn-sm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Create NPC
        </button>
      </div>
    `
  }

  /**
   * Render filter controls
   */
  renderFilters() {
    return `
      <div class="npc-filters">
        <div class="npc-filter-group">
          <label for="npc-filter-type">Type:</label>
          <select id="npc-filter-type" class="npc-filter-select">
            <option value="">All Types</option>
            ${Object.entries(NPC_TYPES).map(([value, config]) => `
              <option value="${value}" ${this.filterType === value ? 'selected' : ''}>
                ${config.icon} ${config.label}
              </option>
            `).join('')}
          </select>
        </div>
        <div class="npc-filter-group">
          <label for="npc-filter-status">Status:</label>
          <select id="npc-filter-status" class="npc-filter-select">
            <option value="">All Statuses</option>
            <option value="ACTIVE" ${this.filterStatus === 'ACTIVE' ? 'selected' : ''}>Active Only</option>
            ${Object.entries(NPC_STATUSES).map(([value, config]) => `
              <option value="${value}" ${this.filterStatus === value && value !== 'ACTIVE' ? 'selected' : ''}>
                ${config.label}
              </option>
            `).join('')}
          </select>
        </div>
      </div>
    `
  }

  /**
   * Render the main content area
   */
  renderContent() {
    if (this.isLoading) {
      return this.renderLoading()
    }

    if (this.error) {
      return this.renderError()
    }

    if (this.npcs.length === 0) {
      return this.renderEmpty()
    }

    return this.renderNPCList()
  }

  /**
   * Render loading state
   */
  renderLoading() {
    return `
      <div class="npc-loading">
        <div class="npc-loading-spinner"></div>
        <p>Loading NPCs...</p>
      </div>
    `
  }

  /**
   * Render error state
   */
  renderError() {
    return `
      <div class="npc-error">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <p>${escapeHtml(this.error)}</p>
        <button id="npc-retry-btn" class="btn btn-ghost btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
          Retry
        </button>
      </div>
    `
  }

  /**
   * Render empty state
   */
  renderEmpty() {
    return `
      <div class="npc-empty">
        <div class="npc-empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <line x1="17" y1="11" x2="23" y2="11"></line>
          </svg>
        </div>
        <h4>No NPCs Found</h4>
        <p>Create your first NPC to populate your world with characters.</p>
      </div>
    `
  }

  /**
   * Render the NPC list grouped by type
   */
  renderNPCList() {
    const groupedNPCs = this.groupNPCsByType()

    return `
      <div class="npc-list">
        ${Object.entries(groupedNPCs).map(([type, npcs]) => `
          <div class="npc-type-group">
            <div class="npc-type-header">
              <span class="npc-type-icon">${NPC_TYPES[type]?.icon || '❓'}</span>
              <span class="npc-type-label">${NPC_TYPES[type]?.label || type}</span>
              <span class="npc-type-count">(${npcs.length})</span>
            </div>
            <div class="npc-cards">
              ${npcs.map(npc => this.renderNPCCard(npc)).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    `
  }

  /**
   * Group NPCs by their type
   */
  groupNPCsByType() {
    const groups = {}
    
    this.npcs.forEach(npc => {
      const type = npc.npc_type || 'NEUTRAL'
      if (!groups[type]) {
        groups[type] = []
      }
      groups[type].push(npc)
    })

    return groups
  }

  /**
   * Render a single NPC card
   */
  renderNPCCard(npc) {
    const typeConfig = NPC_TYPES[npc.npc_type] || NPC_TYPES.NEUTRAL
    const statusConfig = NPC_STATUSES[npc.status] || NPC_STATUSES.ACTIVE
    const stats = npc.stats || {}
    const data = npc.data || {}

    return `
      <div class="npc-card ${typeConfig.class}" data-npc-id="${npc.id}">
        <div class="npc-card-header">
          <div class="npc-avatar ${typeConfig.class}">
            <span>${getInitials(npc.name)}</span>
          </div>
          <div class="npc-info">
            <h4 class="npc-name">${escapeHtml(npc.name)}</h4>
            <div class="npc-badges">
              <span class="npc-type-badge ${typeConfig.class}">${typeConfig.label}</span>
              <span class="npc-status-badge ${statusConfig.class}">${statusConfig.label}</span>
            </div>
          </div>
          <div class="npc-card-actions">
            <button class="npc-action-btn npc-edit-btn" data-npc-id="${npc.id}" title="Edit NPC">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
            <button class="npc-action-btn npc-delete-btn" data-npc-id="${npc.id}" title="Delete NPC">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        </div>

        ${npc.description ? `
          <p class="npc-description">${escapeHtml(npc.description)}</p>
        ` : ''}

        <div class="npc-quick-stats">
          ${stats.hp !== undefined ? `
            <div class="npc-stat">
              <span class="npc-stat-value">${stats.hp}</span>
              <span class="npc-stat-label">HP</span>
            </div>
          ` : ''}
          ${stats.ac !== undefined ? `
            <div class="npc-stat">
              <span class="npc-stat-value">${stats.ac}</span>
              <span class="npc-stat-label">AC</span>
            </div>
          ` : ''}
          ${stats.attack_bonus !== undefined ? `
            <div class="npc-stat">
              <span class="npc-stat-value">+${stats.attack_bonus}</span>
              <span class="npc-stat-label">ATK</span>
            </div>
          ` : ''}
          ${stats.damage !== undefined ? `
            <div class="npc-stat">
              <span class="npc-stat-value">${stats.damage}</span>
              <span class="npc-stat-label">DMG</span>
            </div>
          ` : ''}
        </div>

        ${npc.status === 'ACTIVE' ? `
          <div class="npc-dice-toolbar">
            <button class="dice-btn" data-dice="1d4" data-npc-id="${npc.id}" title="Roll d4">d4</button>
            <button class="dice-btn" data-dice="1d6" data-npc-id="${npc.id}" title="Roll d6">d6</button>
            <button class="dice-btn" data-dice="1d8" data-npc-id="${npc.id}" title="Roll d8">d8</button>
            <button class="dice-btn" data-dice="1d10" data-npc-id="${npc.id}" title="Roll d10">d10</button>
            <button class="dice-btn" data-dice="1d12" data-npc-id="${npc.id}" title="Roll d12">d12</button>
            <button class="dice-btn dice-btn-primary" data-dice="1d20" data-npc-id="${npc.id}" title="Roll d20">d20</button>
            <button class="dice-btn" data-dice="1d100" data-npc-id="${npc.id}" title="Roll d100">d100</button>
          </div>

          <div class="npc-card-footer">
            <button class="btn btn-ghost btn-xs npc-turn-btn" data-npc-id="${npc.id}" title="Give turn to ${escapeHtml(npc.name)}">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              Give Turn
            </button>
            <button class="btn btn-ghost btn-xs npc-convert-btn" data-npc-id="${npc.id}">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <polyline points="17 11 19 13 23 9"></polyline>
              </svg>
              Convert to PC
            </button>
          </div>
        ` : ''}
      </div>
    `
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    // Create NPC button
    document.getElementById('create-npc-btn')?.addEventListener('click', () => {
      this.openNPCForm()
    })

    // Retry button
    document.getElementById('npc-retry-btn')?.addEventListener('click', () => {
      this.loadNPCs()
    })

    // Filter selects
    document.getElementById('npc-filter-type')?.addEventListener('change', (e) => {
      this.filterType = e.target.value || null
      this.loadNPCs()
    })

    document.getElementById('npc-filter-status')?.addEventListener('change', (e) => {
      this.filterStatus = e.target.value || null
      this.loadNPCs()
    })

    // NPC card actions
    document.querySelectorAll('.npc-edit-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const npcId = parseInt(btn.dataset.npcId)
        this.openNPCForm(npcId)
      })
    })

    document.querySelectorAll('.npc-delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const npcId = parseInt(btn.dataset.npcId)
        this.confirmDeleteNPC(npcId)
      })
    })

    document.querySelectorAll('.npc-convert-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const npcId = parseInt(btn.dataset.npcId)
        this.openConvertToPC(npcId)
      })
    })

    // NPC dice buttons
    this.setupNPCDiceButtons()

    // NPC turn buttons
    this.setupNPCTurnButtons()
  }

  /**
   * Open the NPC creation/edit form modal
   */
  openNPCForm(npcId = null) {
    this.editingNPC = npcId ? this.npcs.find(n => n.id === npcId) : null
    this.ensureFormModalExists()
    this.renderFormModal()
    this.showFormModal()
  }

  /**
   * Ensure the form modal exists in the DOM
   */
  ensureFormModalExists() {
    if (!document.getElementById(FORM_MODAL_ID)) {
      document.body.insertAdjacentHTML('beforeend', `
        <div id="${FORM_MODAL_ID}" class="npc-form-overlay" hidden>
          <div class="npc-form-modal">
            <div class="npc-form-header">
              <h2 id="npc-form-title">Create NPC</h2>
              <button id="npc-form-close" class="npc-form-close" type="button">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="npc-form-body" id="npc-form-content">
              <!-- Form content rendered dynamically -->
            </div>
          </div>
        </div>
      `)
    }
  }

  /**
   * Render the form modal content
   */
  renderFormModal() {
    const isEditing = this.editingNPC !== null
    const npc = this.editingNPC || {}
    const stats = npc.stats || {}

    document.getElementById('npc-form-title').textContent = isEditing ? 'Edit NPC' : 'Create NPC'

    const formContent = document.getElementById('npc-form-content')
    formContent.innerHTML = `
      <form id="npc-form" class="npc-form">
        <!-- Basic Info -->
        <div class="npc-form-section">
          <h3 class="npc-form-section-title">Basic Information</h3>
          
          <div class="npc-form-row">
            <div class="npc-form-field">
              <label for="npc-name">Name *</label>
              <input 
                type="text" 
                id="npc-name" 
                name="name" 
                value="${escapeHtml(npc.name || '')}"
                placeholder="Enter NPC name"
                required 
                maxlength="255"
              />
            </div>
          </div>

          <div class="npc-form-row npc-form-row-2">
            <div class="npc-form-field">
              <label for="npc-type">Type *</label>
              <select id="npc-type" name="npc_type" required>
                ${Object.entries(NPC_TYPES).map(([value, config]) => `
                  <option value="${value}" ${npc.npc_type === value ? 'selected' : ''}>
                    ${config.icon} ${config.label}
                  </option>
                `).join('')}
              </select>
            </div>
            
            ${isEditing ? `
              <div class="npc-form-field">
                <label for="npc-status">Status</label>
                <select id="npc-status" name="status">
                  ${Object.entries(NPC_STATUSES).map(([value, config]) => `
                    <option value="${value}" ${npc.status === value ? 'selected' : ''}>
                      ${config.label}
                    </option>
                  `).join('')}
                </select>
              </div>
            ` : ''}
          </div>

          <div class="npc-form-field">
            <label for="npc-description">Description</label>
            <textarea 
              id="npc-description" 
              name="description" 
              placeholder="Describe the NPC's appearance, personality, role..."
              rows="3"
              maxlength="1000"
            >${escapeHtml(npc.description || '')}</textarea>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="npc-form-section">
          <h3 class="npc-form-section-title">Combat Stats</h3>
          
          <div class="npc-form-row npc-form-row-4">
            <div class="npc-form-field">
              <label for="npc-hp">HP</label>
              <input 
                type="number" 
                id="npc-hp" 
                name="hp" 
                value="${stats.hp || ''}"
                placeholder="10"
                min="1"
                max="9999"
              />
            </div>
            
            <div class="npc-form-field">
              <label for="npc-ac">AC</label>
              <input 
                type="number" 
                id="npc-ac" 
                name="ac" 
                value="${stats.ac || ''}"
                placeholder="10"
                min="1"
                max="30"
              />
            </div>
            
            <div class="npc-form-field">
              <label for="npc-attack">Attack Bonus</label>
              <input 
                type="number" 
                id="npc-attack" 
                name="attack_bonus" 
                value="${stats.attack_bonus || ''}"
                placeholder="0"
                min="-10"
                max="30"
              />
            </div>
            
            <div class="npc-form-field">
              <label for="npc-damage">Damage</label>
              <input 
                type="text" 
                id="npc-damage" 
                name="damage" 
                value="${escapeHtml(stats.damage || '')}"
                placeholder="1d6+2"
                maxlength="50"
              />
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="npc-form-actions">
          <button type="button" id="npc-form-cancel" class="btn btn-ghost">
            Cancel
          </button>
          <button type="submit" id="npc-form-submit" class="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            ${isEditing ? 'Save Changes' : 'Create NPC'}
          </button>
        </div>
      </form>
    `

    this.setupFormEventListeners()
  }

  /**
   * Setup form event listeners
   */
  setupFormEventListeners() {
    const form = document.getElementById('npc-form')
    const closeBtn = document.getElementById('npc-form-close')
    const cancelBtn = document.getElementById('npc-form-cancel')
    const overlay = document.getElementById(FORM_MODAL_ID)

    form?.addEventListener('submit', (e) => {
      e.preventDefault()
      this.handleFormSubmit()
    })

    closeBtn?.addEventListener('click', () => this.hideFormModal())
    cancelBtn?.addEventListener('click', () => this.hideFormModal())

    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) {
        this.hideFormModal()
      }
    })

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !overlay?.hidden) {
        this.hideFormModal()
      }
    })
  }

  /**
   * Handle form submission
   */
  async handleFormSubmit() {
    const form = document.getElementById('npc-form')
    const submitBtn = document.getElementById('npc-form-submit')
    
    if (!form) return

    const formData = new FormData(form)
    const name = formData.get('name')?.toString().trim()
    const npc_type = formData.get('npc_type')?.toString()
    const status = formData.get('status')?.toString()
    const description = formData.get('description')?.toString().trim()

    // Build stats object
    const stats = {}
    const hp = formData.get('hp')
    const ac = formData.get('ac')
    const attack_bonus = formData.get('attack_bonus')
    const damage = formData.get('damage')?.toString().trim()

    if (hp) stats.hp = parseInt(hp)
    if (ac) stats.ac = parseInt(ac)
    if (attack_bonus) stats.attack_bonus = parseInt(attack_bonus)
    if (damage) stats.damage = damage

    const payload = {
      name,
      npc_type,
      description: description || null,
      stats,
      data: {}
    }

    if (this.editingNPC && status) {
      payload.status = status
    }

    submitBtn.disabled = true
    submitBtn.innerHTML = `
      <span class="npc-form-spinner"></span>
      ${this.editingNPC ? 'Saving...' : 'Creating...'}
    `

    try {
      let response
      if (this.editingNPC) {
        response = await fetchWithAuth(
          `/api/v1/game/${this.gameId}/npc/${this.editingNPC.id}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }
        )
      } else {
        response = await fetchWithAuth(
          `/api/v1/game/${this.gameId}/npc`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }
        )
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to save NPC')
      }

      const savedNPC = await response.json()

      this.hideFormModal()
      this.onSuccess(this.editingNPC ? 'NPC updated successfully!' : 'NPC created successfully!')
      
      if (this.editingNPC) {
        if (this.onNPCUpdated) this.onNPCUpdated(savedNPC)
      } else {
        if (this.onNPCCreated) this.onNPCCreated(savedNPC)
      }

      await this.loadNPCs()
    } catch (error) {
      this.onError(error.message)
    } finally {
      submitBtn.disabled = false
      submitBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        ${this.editingNPC ? 'Save Changes' : 'Create NPC'}
      `
    }
  }

  /**
   * Confirm and delete an NPC
   */
  async confirmDeleteNPC(npcId) {
    const npc = this.npcs.find(n => n.id === npcId)
    if (!npc) return

    const confirmed = window.confirm(
      `Are you sure you want to delete "${npc.name}"?\n\nThis action cannot be undone.`
    )

    if (!confirmed) return

    try {
      const response = await fetchWithAuth(
        `/api/v1/game/${this.gameId}/npc/${npcId}`,
        { method: 'DELETE' }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to delete NPC')
      }

      this.onSuccess('NPC deleted successfully!')
      if (this.onNPCDeleted) this.onNPCDeleted(npcId)
      await this.loadNPCs()
    } catch (error) {
      this.onError(error.message)
    }
  }

  /**
   * Open convert to PC dialog
   */
  async openConvertToPC(npcId) {
    const npc = this.npcs.find(n => n.id === npcId)
    if (!npc) return

    // For now, just show an alert - in the future this could be a modal
    // that lets the DM select which player will receive the character
    const userId = window.prompt(
      `Convert "${npc.name}" to a player character.\n\nEnter the User ID of the player who will control this character:`
    )

    if (!userId) return

    const userIdNum = parseInt(userId)
    if (isNaN(userIdNum)) {
      this.onError('Invalid user ID')
      return
    }

    try {
      const response = await fetchWithAuth(
        `/api/v1/game/${this.gameId}/npc/${npcId}/convert-to-character`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userIdNum })
        }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to convert NPC')
      }

      this.onSuccess(`${npc.name} has been converted to a player character!`)
      await this.loadNPCs()
    } catch (error) {
      this.onError(error.message)
    }
  }

  /**
   * Show the form modal
   */
  showFormModal() {
    const modal = document.getElementById(FORM_MODAL_ID)
    if (modal) {
      modal.hidden = false
      document.body.style.overflow = 'hidden'
      document.getElementById('npc-name')?.focus()
    }
  }

  /**
   * Hide the form modal
   */
  hideFormModal() {
    const modal = document.getElementById(FORM_MODAL_ID)
    if (modal) {
      modal.hidden = true
      document.body.style.overflow = ''
    }
    this.editingNPC = null
  }

  /**
   * Setup dice button event listeners for NPCs
   */
  setupNPCDiceButtons() {
    const npcDiceButtons = document.querySelectorAll('.npc-dice-toolbar .dice-btn')
    npcDiceButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const formula = btn.dataset.dice
        const npcId = btn.dataset.npcId
        const npc = this.npcs.find(n => n.id === parseInt(npcId))
        if (npc) {
          this.performNPCRoll(formula, npc)
        }
      })
    })
  }

  /**
   * Perform a dice roll for an NPC
   * @param {string} formula - Dice formula (e.g., "1d20")
   * @param {Object} npc - NPC object
   */
  async performNPCRoll(formula, npc) {
    if (!this.socketClient) {
      console.error('[NPCManager] No socket client available for dice roll')
      this.onError('Socket connection not available. Please wait a moment and try again.')
      return
    }

    try {
      // Roll the dice
      const result = DiceService.roll(formula)
      DiceService.showRollResult(result, `${npc.name} Roll`)
      
      // Format content for chat message
      const rollDetails = result.rolls.join(' + ')
      const modifierText = result.modifier !== 0 
        ? (result.modifier > 0 ? ` + ${result.modifier}` : ` - ${Math.abs(result.modifier)}`) 
        : ''
      const content = `rolled ${formula}: ${result.total} (${rollDetails}${modifierText})`
      
      console.log('[NPCManager] Sending NPC dice roll:', { npc: npc.id, formula, result: result.total })
      
      // Send with NPC context
      this.socketClient.sendChatMessage(parseInt(this.gameId), content, {
        message_type: 'dice',
        npc_id: npc.id,
        npc_name: npc.name
      })
    } catch (error) {
      console.error('[NPCManager] Error rolling dice:', error)
      this.onError(`Failed to roll dice: ${error.message}`)
    }
  }

  /**
   * Setup turn button event listeners for NPCs
   */
  setupNPCTurnButtons() {
    const turnButtons = document.querySelectorAll('.npc-card .npc-turn-btn')
    turnButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const npcId = btn.dataset.npcId
        const npc = this.npcs.find(n => n.id === parseInt(npcId))
        if (npc) {
          this.handleSetTurnNPC(npc)
        }
      })
    })
  }

  /**
   * Set turn to an NPC
   * @param {Object} npc - NPC object
   */
  handleSetTurnNPC(npc) {
    if (!this.socketClient) {
      console.error('[NPCManager] No socket client available')
      this.onError('Socket connection not available. Please wait a moment and try again.')
      return
    }

    console.log('[NPCManager] Setting turn to NPC:', npc.id, npc.name)
    this.socketClient.setTurnNPC(
      parseInt(this.gameId),
      npc.id,
      npc.name,
      npc.npc_type
    )
    this.onSuccess(`Turn assigned to ${npc.name}`)
  }

  /**
   * Update the socket client (called after socket connection is ready)
   * @param {Object} socketClient - The socket client instance
   */
  setSocketClient(socketClient) {
    this.socketClient = socketClient
    console.log('[NPCManager] Socket client updated:', !!socketClient)
  }

  /**
   * Refresh the NPC list
   */
  async refresh() {
    await this.loadNPCs()
  }

  /**
   * Destroy the component and cleanup
   */
  destroy() {
    const formModal = document.getElementById(FORM_MODAL_ID)
    if (formModal) {
      formModal.remove()
    }
    document.body.style.overflow = ''
  }
}

