/**
 * Confirm Modal Component
 * A reusable confirmation modal for destructive actions
 */

const MODAL_ID = 'confirm-modal'

const warningIcon = `
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
`

const dangerIcon = `
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="15" y1="9" x2="9" y2="15"></line>
    <line x1="9" y1="9" x2="15" y2="15"></line>
  </svg>
`

const leaveIcon = `
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
    <polyline points="16 17 21 12 16 7"></polyline>
    <line x1="21" y1="12" x2="9" y2="12"></line>
  </svg>
`

const icons = {
  warning: warningIcon,
  danger: dangerIcon,
  leave: leaveIcon
}

function getModalTemplate() {
  return `
    <div id="${MODAL_ID}" class="modal-overlay" hidden>
      <div class="modal-container">
        <div class="modal-header">
          <div id="${MODAL_ID}-icon" class="modal-icon modal-icon-warning"></div>
          <h3 id="${MODAL_ID}-title" class="modal-title"></h3>
        </div>
        <p id="${MODAL_ID}-message" class="modal-message"></p>
        <div class="modal-actions">
          <button id="${MODAL_ID}-cancel" class="btn btn-ghost">Cancel</button>
          <button id="${MODAL_ID}-confirm" class="btn btn-danger-solid">
            <span class="btn-text"></span>
            <span class="btn-loader loader" hidden></span>
          </button>
        </div>
      </div>
    </div>
  `
}

function ensureModalExists() {
  if (!document.getElementById(MODAL_ID)) {
    document.body.insertAdjacentHTML('beforeend', getModalTemplate())
  }
}

function setButtonLoading(button, isLoading) {
  const btnText = button.querySelector('.btn-text')
  const btnLoader = button.querySelector('.btn-loader')
  
  button.disabled = isLoading
  if (btnText) btnText.hidden = isLoading
  if (btnLoader) btnLoader.hidden = !isLoading
}

/**
 * Show a confirmation modal
 * @param {Object} options - Modal configuration
 * @param {string} options.title - Modal title
 * @param {string} options.message - Modal message (can include HTML)
 * @param {string} options.confirmText - Text for confirm button
 * @param {string} options.iconType - Icon type: 'warning', 'danger', 'leave'
 * @param {string} options.iconClass - CSS class for icon styling: 'modal-icon-warning', 'modal-icon-dm'
 * @param {Function} options.onConfirm - Async function to execute on confirm
 * @param {Function} options.onCancel - Optional function to execute on cancel
 * @returns {Promise<boolean>} - Resolves true if confirmed, false if cancelled
 */
export function showConfirmModal(options) {
  ensureModalExists()

  const {
    title,
    message,
    confirmText = 'Confirm',
    iconType = 'warning',
    iconClass = 'modal-icon-warning',
    onConfirm,
    onCancel
  } = options

  const modal = document.getElementById(MODAL_ID)
  const modalTitle = document.getElementById(`${MODAL_ID}-title`)
  const modalMessage = document.getElementById(`${MODAL_ID}-message`)
  const modalIcon = document.getElementById(`${MODAL_ID}-icon`)
  const cancelBtn = document.getElementById(`${MODAL_ID}-cancel`)
  const confirmBtn = document.getElementById(`${MODAL_ID}-confirm`)
  const confirmBtnText = confirmBtn.querySelector('.btn-text')

  modalTitle.textContent = title
  modalMessage.innerHTML = message
  confirmBtnText.textContent = confirmText
  modalIcon.innerHTML = icons[iconType] || icons.warning
  modalIcon.className = `modal-icon ${iconClass}`

  modal.hidden = false

  return new Promise((resolve) => {
    const handleCancel = () => {
      modal.hidden = true
      cleanup()
      if (onCancel) onCancel()
      resolve(false)
    }

    const handleConfirm = async () => {
      setButtonLoading(confirmBtn, true)

      try {
        if (onConfirm) {
          await onConfirm()
        }
        modal.hidden = true
        cleanup()
        resolve(true)
      } catch (error) {
        setButtonLoading(confirmBtn, false)
        modal.hidden = true
        cleanup()
        throw error
      }
    }

    const handleOverlayClick = (event) => {
      if (event.target === modal) {
        handleCancel()
      }
    }

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        handleCancel()
      }
    }

    const cleanup = () => {
      cancelBtn.removeEventListener('click', handleCancel)
      confirmBtn.removeEventListener('click', handleConfirm)
      modal.removeEventListener('click', handleOverlayClick)
      document.removeEventListener('keydown', handleEscape)
      setButtonLoading(confirmBtn, false)
    }

    cancelBtn.addEventListener('click', handleCancel)
    confirmBtn.addEventListener('click', handleConfirm)
    modal.addEventListener('click', handleOverlayClick)
    document.addEventListener('keydown', handleEscape)
  })
}

