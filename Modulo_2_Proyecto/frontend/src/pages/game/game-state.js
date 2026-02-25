/**
 * Shared state for the game page
 * All game-related modules can import and modify this state
 */
export const gameState = {
  currentGame: null,
  currentUserRole: null,
  currentUser: null,
  currentCharacter: null,
  currentTurn: null, // { turn_type, user_id/npc_id, character_name, set_by }
  gameChat: null,
  characterCreator: null,
  characterSheet: null,
  npcManager: null,
  unsubscribeRouteChange: null,
  pendingCharacters: []
}

/**
 * Reset all state to initial values
 * Useful for cleanup when leaving the game page
 */
export function resetGameState() {
  gameState.currentGame = null
  gameState.currentUserRole = null
  gameState.currentUser = null
  gameState.currentCharacter = null
  gameState.currentTurn = null
  gameState.gameChat = null
  gameState.characterCreator = null
  gameState.characterSheet = null
  gameState.npcManager = null
  gameState.unsubscribeRouteChange = null
  gameState.pendingCharacters = []
}
