/**
 * NPCFormManager
 * 
 * Handles NPC creation and editing form modal.
 */

import { fetchWithAuth, escapeHtml } from '../../utils/index.js'
import { NPC_TYPES, NPC_STATUSES, FORM_MODAL_ID } from './npc-constants.js'

export class NPCFormManager {
  constructor(manager) {
    this.manager = manager
    this.editingNPC = null
  }

  /**
   * Open the NPC creation/edit form modal
   */
  openNPCForm(npcId = null) {
    this.editingNPC = npcId ? this.manager.npcs.find(n => n.id === npcId) : null
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
          `/api/v1/game/${this.manager.gameId}/npc/${this.editingNPC.id}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }
        )
      } else {
        response = await fetchWithAuth(
          `/api/v1/game/${this.manager.gameId}/npc`,
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
      this.manager.onSuccess(this.editingNPC ? 'NPC updated successfully!' : 'NPC created successfully!')
      
      if (this.editingNPC) {
        if (this.manager.onNPCUpdated) this.manager.onNPCUpdated(savedNPC)
      } else {
        if (this.manager.onNPCCreated) this.manager.onNPCCreated(savedNPC)
      }

      await this.manager.loadNPCs()
    } catch (error) {
      this.manager.onError(error.message)
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
   * Cleanup on destroy
   */
  destroy() {
    const formModal = document.getElementById(FORM_MODAL_ID)
    if (formModal) {
      formModal.remove()
    }
    document.body.style.overflow = ''
  }
}
