/**
 * UI Message functions
 * Handles displaying error, success, and modal messages
 */

function showMessage(elementId, message, autoHideDelay = null) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = message;
    element.style.display = "block";
    
    if (autoHideDelay) {
        setTimeout(() => {
            element.style.display = "none";
        }, autoHideDelay);
    }
}

function showError(message, autoHideDelay = null) {
    showMessage("error-message", message, autoHideDelay);
}

function showSuccess(message, autoHideDelay = null) {
    showMessage("success-message", message, autoHideDelay);
}

function showErrorModal(message, autoHideDelay = 3000) {
    showMessage("error-message-modal", message, autoHideDelay);
}

function hideMessages() {
    const messageIds = ["error-message", "success-message", "error-message-modal"];
    messageIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.style.display = "none";
    });
}

