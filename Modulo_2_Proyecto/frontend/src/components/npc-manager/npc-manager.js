/**
 * NPCManager Component
 * 
 * Main orchestrator for NPC management.
 * Panel exclusive for DM with complete CRUD operations for NPCs.
 * Allows creating, editing, and deleting NPCs.
 */

import { fetchWithAuth } from '../../utils/index.js'
import { NPCRenderer } from './npc-renderer.js'
import { NPCFormManager } from './npc-form-manager.js'
import { NPCActions } from './npc-actions.js'

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
    this.filterType = null
    this.filterStatus = 'ACTIVE'

    this.renderer = new NPCRenderer(this)
    this.formManager = new NPCFormManager(this)
    this.actions = new NPCActions(this)
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
        ${this.renderer.renderHeader()}
        ${this.renderer.renderFilters()}
        ${this.renderer.renderContent()}
      </div>
    `

    this.setupEventListeners()
  }

  /**
   * Setup all event listeners
   */
  setupEventListeners() {
    document.getElementById('create-npc-btn')?.addEventListener('click', () => {
      this.formManager.openNPCForm()
    })

    document.getElementById('npc-retry-btn')?.addEventListener('click', () => {
      this.loadNPCs()
    })

    document.getElementById('npc-filter-type')?.addEventListener('change', (e) => {
      this.filterType = e.target.value || null
      this.loadNPCs()
    })

    document.getElementById('npc-filter-status')?.addEventListener('change', (e) => {
      this.filterStatus = e.target.value || null
      this.loadNPCs()
    })

    document.querySelectorAll('.npc-edit-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const npcId = parseInt(btn.dataset.npcId)
        this.formManager.openNPCForm(npcId)
      })
    })

    document.querySelectorAll('.npc-delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation()
        const npcId = parseInt(btn.dataset.npcId)
        this.actions.confirmDeleteNPC(npcId)
      })
    })

    this.actions.setupNPCDiceButtons()
    this.actions.setupNPCTurnButtons()
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
    this.formManager.destroy()
    document.body.style.overflow = ''
  }
}
