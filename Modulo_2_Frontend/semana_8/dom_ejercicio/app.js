const API_URL = "https://api.restful-api.dev/objects";

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

function showError(message) {
    const errorEl = document.getElementById("error-message");
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = "block";
    }
}

function showSuccess(message) {
    const successEl = document.getElementById("success-message");
    if (successEl) {
        successEl.textContent = message;
        successEl.style.display = "block";
    }
}

function hideMessages() {
    const errorEl = document.getElementById("error-message");
    const successEl = document.getElementById("success-message");
    if (errorEl) errorEl.style.display = "none";
    if (successEl) successEl.style.display = "none";
}

async function registerUser(event) {
    event.preventDefault();
    hideMessages();

    const nombre = document.getElementById("nombre").value;
    const correo = document.getElementById("correo").value;
    const password = document.getElementById("password").value;
    const direccion = document.getElementById("direccion").value;

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: nombre,
                data: {
                    email: correo,
                    password: password,
                    address: direccion
                }
            })
        });

        if (!response.ok) {
            showError("Error al crear el usuario. Intenta de nuevo.");
            return;
        }

        const result = await response.json();
        
        saveSession(result);
        
        alert(`Usuario creado correctamente! Tu id es ${result.id}`);
        
        window.location.href = "perfil.html";

    } catch (error) {
        showError("Error de conexión. Intenta de nuevo.");
    }
}

async function loginUser(event) {
    event.preventDefault();
    hideMessages();

    const userId = document.getElementById("userId").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${API_URL}/${userId}`);

        if (response.status === 404) {
            showError("Usuario no encontrado.");
            return;
        }

        const user = await response.json();

        if (!user.data || user.data.password !== password) {
            showError("Contraseña incorrecta.");
            return;
        }

        saveSession(user);
        
        window.location.href = "perfil.html";

    } catch (error) {
        showError("Error de conexión. Intenta de nuevo.");
    }
}

function loadProfile() {
    if (!isLoggedIn()) {
        window.location.href = "login.html";
        return;
    }

    const user = getSession();
    const profileContent = document.getElementById("profile-content");

    if (profileContent && user) {
        let dataHtml = "";
        
        if (user.data) {
            for (const [key, value] of Object.entries(user.data)) {
                if (key !== "password") {
                    dataHtml += `<div class="profile-item"><strong>${key}:</strong> ${value}</div>`;
                }
            }
        }

        profileContent.innerHTML = `
            <div class="profile-card">
                <h2>${user.name || "Usuario"}</h2>
                <div class="profile-item"><strong>ID:</strong> ${user.id}</div>
                ${dataHtml}
            </div>
        `;
    }
}

function logout() {
    clearSession();
    window.location.href = "login.html";
}

async function changePassword(event) {
    event.preventDefault();
    hideMessages();

    const userId = document.getElementById("userId").value;
    const oldPassword = document.getElementById("oldPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (newPassword !== confirmPassword) {
        showError("Las contraseñas nuevas no coinciden.");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/${userId}`);

        if (response.status === 404) {
            showError("Usuario no encontrado.");
            return;
        }

        const user = await response.json();

        if (!user.data || user.data.password !== oldPassword) {
            showError("La contraseña anterior es incorrecta.");
            return;
        }

        const updateResponse = await fetch(`${API_URL}/${userId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data: {
                    ...user.data,
                    password: newPassword
                }
            })
        });

        if (!updateResponse.ok) {
            showError("Error al actualizar la contraseña.");
            return;
        }

        showSuccess("Contraseña actualizada correctamente!");
        
        document.getElementById("change-password-form").reset();

    } catch (error) {
        showError("Error de conexión. Intenta de nuevo.");
    }
}

function checkSessionAndRedirect() {
    if (isLoggedIn()) {
        window.location.href = "perfil.html";
    }
}
