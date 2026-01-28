/**
 * NPCRenderer
 * 
 * Handles all rendering logic for NPC Manager UI.
 */

import { escapeHtml, getInitials } from '../../utils/index.js'
import { NPC_TYPES, NPC_STATUSES } from './npc-constants.js'

export class NPCRenderer {
  constructor(manager) {
    this.manager = manager
  }

  /**
   * Render the header with title and create button
   */
  renderHeader() {
    const npcs = this.manager.npcs
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
          <span class="npc-count">${npcs.length} NPC${npcs.length !== 1 ? 's' : ''}</span>
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
    const filterType = this.manager.filterType
    const filterStatus = this.manager.filterStatus
    
    return `
      <div class="npc-filters">
        <div class="npc-filter-group">
          <label for="npc-filter-type">Type:</label>
          <select id="npc-filter-type" class="npc-filter-select">
            <option value="">All Types</option>
            ${Object.entries(NPC_TYPES).map(([value, config]) => `
              <option value="${value}" ${filterType === value ? 'selected' : ''}>
                ${config.icon} ${config.label}
              </option>
            `).join('')}
          </select>
        </div>
        <div class="npc-filter-group">
          <label for="npc-filter-status">Status:</label>
          <select id="npc-filter-status" class="npc-filter-select">
            <option value="">All Statuses</option>
            <option value="ACTIVE" ${filterStatus === 'ACTIVE' ? 'selected' : ''}>Active Only</option>
            ${Object.entries(NPC_STATUSES).map(([value, config]) => `
              <option value="${value}" ${filterStatus === value && value !== 'ACTIVE' ? 'selected' : ''}>
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
    if (this.manager.isLoading) {
      return this.renderLoading()
    }

    if (this.manager.error) {
      return this.renderError()
    }

    if (this.manager.npcs.length === 0) {
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
        <p>${escapeHtml(this.manager.error)}</p>
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
    
    this.manager.npcs.forEach(npc => {
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
          </div>
        ` : ''}
      </div>
    `
  }
}
