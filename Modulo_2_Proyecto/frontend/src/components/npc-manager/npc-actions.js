/**
 * NPCActions
 * 
 * Handles NPC interactive actions like dice rolls, turns, and deletion.
 */

import { fetchWithAuth } from '../../utils/index.js'
import { DiceService } from '../../utils/dice-service.js'

export class NPCActions {
  constructor(manager) {
    this.manager = manager
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
        const npc = this.manager.npcs.find(n => n.id === parseInt(npcId))
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
    if (!this.manager.socketClient) {
      console.error('[NPCManager] No socket client available for dice roll')
      this.manager.onError('Socket connection not available. Please wait a moment and try again.')
      return
    }

    try {
      const result = DiceService.roll(formula)
      DiceService.showRollResult(result, `${npc.name} Roll`)
      
      const rollDetails = result.rolls.join(' + ')
      const modifierText = result.modifier !== 0 
        ? (result.modifier > 0 ? ` + ${result.modifier}` : ` - ${Math.abs(result.modifier)}`) 
        : ''
      const content = `rolled ${formula}: ${result.total} (${rollDetails}${modifierText})`
      
      console.log('[NPCManager] Sending NPC dice roll:', { npc: npc.id, formula, result: result.total })
      
      this.manager.socketClient.sendChatMessage(parseInt(this.manager.gameId), content, {
        message_type: 'dice',
        npc_id: npc.id,
        npc_name: npc.name
      })
    } catch (error) {
      console.error('[NPCManager] Error rolling dice:', error)
      this.manager.onError(`Failed to roll dice: ${error.message}`)
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
        const npc = this.manager.npcs.find(n => n.id === parseInt(npcId))
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
    if (!this.manager.socketClient) {
      console.error('[NPCManager] No socket client available')
      this.manager.onError('Socket connection not available. Please wait a moment and try again.')
      return
    }

    console.log('[NPCManager] Setting turn to NPC:', npc.id, npc.name)
    this.manager.socketClient.setTurnNPC(
      parseInt(this.manager.gameId),
      npc.id,
      npc.name,
      npc.npc_type
    )
    this.manager.onSuccess(`Turn assigned to ${npc.name}`)
  }

  /**
   * Confirm and delete an NPC
   */
  async confirmDeleteNPC(npcId) {
    const npc = this.manager.npcs.find(n => n.id === npcId)
    if (!npc) return

    const confirmed = window.confirm(
      `Are you sure you want to delete "${npc.name}"?\n\nThis action cannot be undone.`
    )

    if (!confirmed) return

    try {
      const response = await fetchWithAuth(
        `/api/v1/game/${this.manager.gameId}/npc/${npcId}`,
        { method: 'DELETE' }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Failed to delete NPC')
      }

      this.manager.onSuccess('NPC deleted successfully!')
      if (this.manager.onNPCDeleted) this.manager.onNPCDeleted(npcId)
      await this.manager.loadNPCs()
    } catch (error) {
      this.manager.onError(error.message)
    }
  }
}
