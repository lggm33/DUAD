const API_URL = "https://api.restful-api.dev/objects";

function saveSession(userData) {
    localStorage.setItem("userSession", JSON.stringify(userData));
}

function getSession() {
    const data = localStorage.getItem("userSession");
    console.log({data});
    return data ? JSON.parse(data) : null;
}

function clearSession() {
    localStorage.removeItem("userSession");
}

function isLoggedIn() {
    return getSession() !== null;
}

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
                    address: direccion,
                    tasks: []
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
                if (key !== "password" && key !== "tasks") {
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

function showAddTaskForm(isEditMode = false, taskId = null) {
    const modal = document.getElementById("add-task-form-modal");
    const form = document.getElementById("add-task-form");
    const modalTitle = modal.querySelector("h2");
    const submitBtn = form.querySelector("button[type='submit']");

    if (isEditMode) {
        modalTitle.textContent = "Editar Tarea";
        submitBtn.textContent = "Guardar";
        form.dataset.editTaskId = taskId;
    } else {
        modalTitle.textContent = "Agregar Tarea";
        submitBtn.textContent = "Agregar";
        delete form.dataset.editTaskId;
    }

    modal.style.display = "block";
}

function closeAddTaskForm() {
    const form = document.getElementById("add-task-form");
    form.reset();
    delete form.dataset.editTaskId;
    document.getElementById("add-task-form-modal").style.display = "none";
}

async function loadTasks() {

    console.log("loadTasks");

    if (!isLoggedIn()) {
        window.location.href = "login.html";
        return;
    }
    const tasksContent = document.getElementById("tasks-list");
    tasksContent.innerHTML = "<p>Cargando...</p>";

    const user = getSession();
    try {
        const tasksIds = user.data.tasks.map(task => `id=${task}`).join("&");

        if (tasksIds.length === 0) {
            tasksContent.innerHTML = "<p>No hay tareas para mostrar.</p>";
            return;
        }

        const tasks = await fetch(`${API_URL}?${tasksIds}`);
        const tasksData = await tasks.json();

        const tasksElements = tasksData.map(task => createTaskElement(task));

        tasksContent.innerHTML = "";

        tasksElements.forEach(element => {
            tasksContent.appendChild(element);
        })

    } catch (error) {
        tasksContent.innerHTML = "";
        showError("Error al cargar las tareas. Intenta mas tarde.");
    }
}

async function manageTask(event) {
    event.preventDefault();

    const user = getSession();

    const form = document.getElementById("add-task-form");
    const title = document.getElementById("title").value;
    const description = document.getElementById("description").value;
    const state = document.getElementById("state").value;
    
    try {
        
        if (form.dataset.editTaskId) {
            await updateTask(form.dataset.editTaskId, title, description, state);
        } else {
            await createTask(user, title, description, state);
        }

        document.getElementById("add-task-form").reset();
        closeAddTaskForm();
        loadTasks();
    } catch (error) {
        showErrorModal(error.message);
    }

}

async function createTask(user, title, description, state) {

    const  responseCreateTask = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            data: {
                title: title,
                description: description,
                state: state
            }
        })
    });

    if (!responseCreateTask.ok) {
        throw new Error("Error al crear la tarea. Intenta de nuevo.");
    }

    const result = await responseCreateTask.json();

    const responseAddTaskToUser = await fetch(`${API_URL}/${user.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: user.name,
            data: {
                ...user.data,
                tasks: [...user.data.tasks, result.id]
            }
        })
    });


    if (!responseAddTaskToUser.ok) {
        throw new Error("Error al agregar la tarea al usuario. Intenta de nuevo.");
    }

    const resultAddTaskToUser = await responseAddTaskToUser.json();



    saveSession(resultAddTaskToUser);
}

async function updateTask(taskId, title, description, state) {

    const responseUpdateTask = await fetch(`${API_URL}/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            data: {
                title: title,
                description: description,
                state: state
            }
        })
    });
    
    if (!responseUpdateTask.ok) {
        throw new Error("Error al actualizar la tarea. Intenta de nuevo.");
    }
}

function createTaskElement(task) {


    const taskItem = document.createElement('div');
    taskItem.className = 'task-item';
    taskItem.dataset.taskId = task.id;

    const title = document.createElement('h3');
    title.id = 'task-title';
    title.textContent = task.data.title;

    const description = document.createElement('p');
    description.id = 'task-description';
    description.textContent = task.data.description;

    const state = document.createElement('span');
    state.id = 'task-state';
    state.textContent = task.data.state;

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'task-actions';

    const editBtn = document.createElement('button');
    editBtn.className = 'btn-icon btn-edit';
    editBtn.title = 'Editar';
    editBtn.innerHTML = getEditSvg();
    editBtn.addEventListener('click', () => openEditTaskForm(task.id));

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-icon btn-delete';
    deleteBtn.title = 'Eliminar';
    deleteBtn.innerHTML = getDeleteSvg();
    deleteBtn.addEventListener('click', () => deleteTask(task.id));

    actionsDiv.appendChild(editBtn);
    actionsDiv.appendChild(deleteBtn);
    
    taskItem.appendChild(title);
    taskItem.appendChild(description);
    taskItem.appendChild(state);
    taskItem.appendChild(actionsDiv);

    return taskItem;
}

function getEditSvg() {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
    </svg>`;
}

function getDeleteSvg() {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="3 6 5 6 21 6"></polyline>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        <line x1="10" y1="11" x2="10" y2="17"></line>
        <line x1="14" y1="11" x2="14" y2="17"></line>
    </svg>`;
}

async function deleteTask(taskId) {
    const user = getSession();

    const body = {
        name: user.name,
        data: {
            ...user.data,
            tasks: user.data.tasks.filter(task => task !== taskId)
        }
    }

    try {

        const responseDeleteTask = await fetch(`${API_URL}/${taskId}`, {
            method: "DELETE",
        });

        if (!responseDeleteTask.ok) {
            showError("Error al eliminar la tarea. Intenta de nuevo.");
            return;
        }

        const result = await responseDeleteTask.json();
        
        saveSession({...user, data: body.data});
        loadTasks();
    } catch (error) {
        showError("Error al eliminar la tarea. Intenta de nuevo.");
    }
}

async function openEditTaskForm(taskId) {

    const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
    
    const currentTitle = taskElement.querySelector('#task-title').textContent;
    const currentDescription = taskElement.querySelector('#task-description').textContent;
    const currentState = taskElement.querySelector('#task-state').textContent;

    showAddTaskForm(true, taskId);

    document.getElementById("title").value = currentTitle;
    document.getElementById("description").value = currentDescription;
    document.getElementById("state").value = currentState;

}