import template from './inventory.html?raw'
import { Footer, showConfirmModal } from '../components/index.js'
import { navigate, getRouteParams, onBeforeRouteChange } from '../router.js'
import { fetchWithAuth, escapeHtml } from '../utils/index.js'

let currentGameId = null
let currentCharacterId = null
let currentCharacter = null
let inventoryItems = []
let editingItemId = null
let unsubscribeRouteChange = null

export function inventoryPage(app) {
  app.innerHTML = template + Footer()
  initInventory()
}

async function initInventory() {
  const { id: gameId } = getRouteParams()
  
  if (!gameId) {
    showError('Invalid game ID')
    return
  }

  currentGameId = gameId

  // Setup route cleanup
  unsubscribeRouteChange = onBeforeRouteChange(() => {
    cleanup()
  })

  // Setup back button
  const backBtn = document.getElementById('back-to-game-btn')
  if (backBtn) {
    backBtn.addEventListener('click', () => {
      navigate(`/game/${gameId}`)
    })
  }

  // Load character and inventory
  await loadCharacterAndInventory()
}

function cleanup() {
  if (unsubscribeRouteChange) {
    unsubscribeRouteChange()
    unsubscribeRouteChange = null
  }
  
  currentGameId = null
  currentCharacterId = null
  currentCharacter = null
  inventoryItems = []
  editingItemId = null
}

async function loadCharacterAndInventory() {
  const loadingEl = document.getElementById('inventory-loading')
  const errorEl = document.getElementById('inventory-error')
  const contentEl = document.getElementById('inventory-content')

  try {
    // Load character first to get character ID
    const charResponse = await fetchWithAuth(`/api/v1/game/${currentGameId}/my-character`)
    
    if (!charResponse.ok) {
      const error = await charResponse.json()
      throw new Error(error.message || 'Failed to load character')
    }

    currentCharacter = await charResponse.json()
    currentCharacterId = currentCharacter.id

    // Update character name in title
    const charNameEl = document.getElementById('character-name')
    if (charNameEl) {
      charNameEl.textContent = currentCharacter.name
    }

    // Load inventory
    await loadInventory()

    loadingEl.hidden = true
    contentEl.hidden = false

    // Setup UI event listeners
    setupEventListeners()

  } catch (error) {
    loadingEl.hidden = true
    errorEl.hidden = false
    document.getElementById('inventory-error-message').textContent = error.message
  }
}

async function loadInventory() {
  try {
    const response = await fetchWithAuth(
      `/api/v1/game/${currentGameId}/character/${currentCharacterId}/inventory`
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to load inventory')
    }

    const data = await response.json()
    inventoryItems = data.inventory || []

    renderInventory()
  } catch (error) {
    console.error('Error loading inventory:', error)
    showMessage(error.message, 'error')
  }
}

function renderInventory() {
  const emptyEl = document.getElementById('inventory-empty')
  const tableContainer = document.getElementById('inventory-table-container')
  const itemsBody = document.getElementById('inventory-items')

  if (inventoryItems.length === 0) {
    emptyEl.hidden = false
    tableContainer.hidden = true
    return
  }

  emptyEl.hidden = true
  tableContainer.hidden = false

  itemsBody.innerHTML = inventoryItems.map(item => `
    <tr data-item-id="${item.id}">
      <td class="item-name">${escapeHtml(item.name)}</td>
      <td class="item-description">${escapeHtml(item.description || '-')}</td>
      <td class="item-quantity">
        <div class="quantity-controls">
          <button type="button" class="quantity-btn" data-action="decrease" data-item-id="${item.id}" ${item.quantity <= 1 ? 'disabled' : ''}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </button>
          <span class="quantity-value">${item.quantity}</span>
          <button type="button" class="quantity-btn" data-action="increase" data-item-id="${item.id}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </button>
        </div>
      </td>
      <td class="item-actions">
        <button type="button" class="btn btn-ghost btn-sm" data-action="edit" data-item-id="${item.id}" title="Edit item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button type="button" class="btn btn-ghost btn-sm btn-danger" data-action="delete" data-item-id="${item.id}" title="Delete item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </td>
    </tr>
  `).join('')

  // Add event listeners to buttons
  setupTableEventListeners()
}

function setupEventListeners() {
  // Add item button
  const addBtn = document.getElementById('add-item-btn')
  if (addBtn) {
    addBtn.addEventListener('click', () => openItemModal())
  }

  // Retry button
  const retryBtn = document.getElementById('retry-load-btn')
  if (retryBtn) {
    retryBtn.addEventListener('click', () => {
      document.getElementById('inventory-error').hidden = true
      document.getElementById('inventory-loading').hidden = false
      loadCharacterAndInventory()
    })
  }

  // Modal buttons
  const closeModalBtn = document.getElementById('close-modal-btn')
  const cancelModalBtn = document.getElementById('cancel-modal-btn')
  const itemForm = document.getElementById('item-form')

  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', (e) => {
      e.preventDefault()
      closeItemModal()
    })
  }

  if (cancelModalBtn) {
    cancelModalBtn.addEventListener('click', (e) => {
      e.preventDefault()
      closeItemModal()
    })
  }

  if (itemForm) {
    itemForm.addEventListener('submit', handleItemFormSubmit)
  }

  // Close modal on backdrop click
  const modal = document.getElementById('item-modal')
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-backdrop')) {
        closeItemModal()
      }
    })
  }
}

function setupTableEventListeners() {
  // Quantity buttons
  document.querySelectorAll('.quantity-btn').forEach(btn => {
    btn.addEventListener('click', handleQuantityChange)
  })

  // Edit buttons
  document.querySelectorAll('[data-action="edit"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const itemId = e.currentTarget.dataset.itemId
      openItemModal(itemId)
    })
  })

  // Delete buttons
  document.querySelectorAll('[data-action="delete"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const itemId = e.currentTarget.dataset.itemId
      handleDeleteItem(itemId)
    })
  })
}

function openItemModal(itemId = null) {
  editingItemId = itemId
  const modal = document.getElementById('item-modal')
  const modalTitle = document.getElementById('modal-title')
  const saveBtnText = document.getElementById('save-btn-text')
  const nameInput = document.getElementById('item-name')
  const descInput = document.getElementById('item-description')
  const qtyInput = document.getElementById('item-quantity')

  if (itemId) {
    // Edit mode
    const item = inventoryItems.find(i => i.id === itemId)
    if (item) {
      modalTitle.textContent = 'Edit Item'
      saveBtnText.textContent = 'Save Changes'
      nameInput.value = item.name
      descInput.value = item.description || ''
      qtyInput.value = item.quantity
    }
  } else {
    // Add mode
    modalTitle.textContent = 'Add Item'
    saveBtnText.textContent = 'Add Item'
    nameInput.value = ''
    descInput.value = ''
    qtyInput.value = 1
  }

  modal.hidden = false
  nameInput.focus()
}

function closeItemModal() {
  const modal = document.getElementById('item-modal')
  const form = document.getElementById('item-form')
  
  if (modal) {
    modal.hidden = true
  }
  if (form) {
    form.reset()
  }
  editingItemId = null
}

async function handleItemFormSubmit(e) {
  e.preventDefault()

  const nameInput = document.getElementById('item-name')
  const descInput = document.getElementById('item-description')
  const qtyInput = document.getElementById('item-quantity')
  const saveBtn = document.getElementById('save-item-btn')
  const saveBtnText = document.getElementById('save-btn-text')
  const saveBtnLoader = document.getElementById('save-btn-loader')

  const name = nameInput.value.trim()
  const description = descInput.value.trim()
  const quantity = parseInt(qtyInput.value, 10)

  if (!name) {
    showMessage('Item name is required', 'error')
    return
  }

  if (quantity < 1) {
    showMessage('Quantity must be at least 1', 'error')
    return
  }

  // Show loading state
  saveBtn.disabled = true
  saveBtnText.hidden = true
  saveBtnLoader.hidden = false

  try {
    if (editingItemId) {
      // Update existing item
      await updateItem(editingItemId, { name, description, quantity })
      showMessage('Item updated successfully', 'success')
    } else {
      // Add new item
      await addItem({ name, description, quantity })
      showMessage('Item added successfully', 'success')
    }

    closeItemModal()
    await loadInventory()
  } catch (error) {
    console.error('Error in form submit:', error)
    showMessage(error.message, 'error')
  } finally {
    saveBtn.disabled = false
    saveBtnText.hidden = false
    saveBtnLoader.hidden = true
  }
}

async function addItem(itemData) {
  const response = await fetchWithAuth(
    `/api/v1/game/${currentGameId}/character/${currentCharacterId}/inventory`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(itemData)
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Failed to add item')
  }

  return await response.json()
}

async function updateItem(itemId, updates) {
  const response = await fetchWithAuth(
    `/api/v1/game/${currentGameId}/character/${currentCharacterId}/inventory/${itemId}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Failed to update item')
  }

  return await response.json()
}

async function handleQuantityChange(e) {
  const btn = e.currentTarget
  const itemId = btn.dataset.itemId
  const action = btn.dataset.action
  
  const item = inventoryItems.find(i => i.id === itemId)
  if (!item) return

  const newQuantity = action === 'increase' ? item.quantity + 1 : item.quantity - 1

  if (newQuantity < 1) return

  try {
    await updateItem(itemId, { quantity: newQuantity })
    await loadInventory()
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

async function handleDeleteItem(itemId) {
  const item = inventoryItems.find(i => i.id === itemId)
  if (!item) return

  const confirmed = await showConfirmModal({
    title: 'Delete Item',
    message: `Are you sure you want to delete "${item.name}"? This action cannot be undone.`,
    confirmText: 'Delete',
    confirmClass: 'btn-danger'
  })

  if (!confirmed) return

  try {
    const response = await fetchWithAuth(
      `/api/v1/game/${currentGameId}/character/${currentCharacterId}/inventory/${itemId}`,
      { method: 'DELETE' }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Failed to delete item')
    }

    showMessage('Item deleted successfully', 'success')
    await loadInventory()
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

function showMessage(message, type = 'info') {
  const messageEl = document.getElementById('inventory-message')
  if (!messageEl) return

  messageEl.textContent = message
  messageEl.className = `inventory-message inventory-message-${type}`
  messageEl.hidden = false

  setTimeout(() => {
    messageEl.hidden = true
  }, 5000)
}

function showError(message) {
  const loadingEl = document.getElementById('inventory-loading')
  const errorEl = document.getElementById('inventory-error')
  const errorMsgEl = document.getElementById('inventory-error-message')

  loadingEl.hidden = true
  errorEl.hidden = false
  if (errorMsgEl) {
    errorMsgEl.textContent = message
  }
}
