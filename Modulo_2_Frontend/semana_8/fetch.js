// Ejercicios de Requests con Fetch
// API: https://api.restful-api.dev/objects

const API_URL = "https://api.restful-api.dev/objects";

// Ejercicio 1: Listar todos los elementos y formatear los que tienen data
async function listAllObjects() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        // Filtrar solo los que tienen data
        const objectsWithData = data.filter(item => item.data !== null && item.data !== undefined);

        // Formatear cada objeto
        objectsWithData.forEach(item => {
            const dataInfo = Object.entries(item.data)
                .map(([key, value]) => `${key}: ${value}`)
                .join(", ");
            
            console.log(`${item.name} (${dataInfo})`);
        });

        return objectsWithData;
    } catch (error) {
        console.error("Error al obtener los objetos:", error.message);
    }
}

// Ejercicio 2: Crear un usuario con POST
async function createUser(nombre, correo, contraseña, direccion) {
    try {
        const userData = {
            name: nombre,
            data: {
                email: correo,
                password: contraseña,
                address: direccion
            }
        };

        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(userData)
        });

        const result = await response.json();
        console.log("Usuario creado:", result);
        console.log("¡IMPORTANTE! Guarda este ID:", result.id);
        
        return result;
    } catch (error) {
        console.error("Error al crear usuario:", error.message);
    }
}

// Ejercicio 3: Obtener un usuario por ID
async function getUserById(id) {
    try {
        const response = await fetch(`${API_URL}/${id}`);

        if (response.status === 404) {
            console.log("Error: Usuario no encontrado");
            return null;
        }

        const user = await response.json();
        console.log("Usuario encontrado:", user);
        return user;
    } catch (error) {
        console.error("Error al buscar usuario:", error.message);
    }
}

// Ejercicio 4: Actualizar la dirección de un usuario
async function updateUserAddress(id, nuevaDireccion) {
    try {
        const response = await fetch(`${API_URL}/${id}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                data: {
                    address: nuevaDireccion
                }
            })
        });

        if (response.status === 404) {
            console.log("Error: Usuario no encontrado");
            return null;
        }

        const result = await response.json();
        console.log("Dirección actualizada:", result);
        return result;
    } catch (error) {
        console.error("Error al actualizar dirección:", error.message);
    }
}

// Ejemplos de uso (descomenta para probar)
// listAllObjects();
// createUser("Juan Perez", "juan@email.com", "123456", "Calle 123");
// getUserById("1");
// updateUserAddress("ff808181932badb601955e190e1c04de", "Nueva Calle 456");

