/**
 * Session management functions
 * Handles user session storage and authentication state
 */

function saveSession(userData) {
    localStorage.setItem("userSession", JSON.stringify(userData));
}

function getSession() {
    const data = localStorage.getItem("userSession");
    return data ? JSON.parse(data) : null;
}

function clearSession() {
    localStorage.removeItem("userSession");
}

function isLoggedIn() {
    return getSession() !== null;
}

function checkSessionAndRedirect() {
    if (isLoggedIn()) {
        window.location.href = "perfil.html";
    }
}

