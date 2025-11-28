// Ejercicios de Requests con Axios
// API: https://api.restful-api.dev/objects

const axios = require('axios');

const API_URL = "https://api.restful-api.dev/objects";

// Ejercicio 1: Listar todos los elementos y formatear los que tienen data
async function listAllObjects() {
    try {
        const response = await axios.get(API_URL);
        const data = response.data;

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

        const response = await axios.post(API_URL, userData);
        
        console.log("Usuario creado:", response.data);
        console.log("¡IMPORTANTE! Guarda este ID:", response.data.id);
        
        return response.data;
    } catch (error) {
        console.error("Error al crear usuario:", error.message);
    }
}

// Ejercicio 3: Obtener un usuario por ID
async function getUserById(id) {
    try {
        const response = await axios.get(`${API_URL}/${id}`);
        console.log("Usuario encontrado:", response.data);
        return response.data;
    } catch (error) {
        if (error.response && error.response.status === 404) {
            console.log("Error: Usuario no encontrado");
            return null;
        }
        console.error("Error al buscar usuario:", error.message);
    }
}

// Ejercicio 4: Actualizar la dirección de un usuario
async function updateUserAddress(id, nuevaDireccion) {
    try {
        const response = await axios.patch(`${API_URL}/${id}`, {
            data: {
                address: nuevaDireccion
            }
        });

        console.log("Dirección actualizada:", response.data);
        return response.data;
    } catch (error) {
        if (error.response && error.response.status === 404) {
            console.log("Error: Usuario no encontrado");
            return null;
        }
        console.error("Error al actualizar dirección:", error.message);
    }
}

// Ejemplos de uso (descomenta para probar)
// listAllObjects();
// createUser("Juan Perez", "juan@email.com", "123456", "Calle 123");
// getUserById("ff8081819782e69e019ac80669432692");
updateUserAddress("ff8081819782e69e019ac80669432692", "Nueva Calle 456");

