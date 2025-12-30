# Gateway (Nginx Reverse Proxy)

El gateway actúa como punto de entrada único para la aplicación, enrutando:
- `/api/*` → Backend (Flask)
- `/*` → Frontend (Vite/React)

## Modos de Operación

| Modo | Uso | Configuración |
|------|-----|---------------|
| **Local sin Docker** | Desarrollo diario | `nginx.conf` + `default.conf` |
| **Local con Docker** | Probar paridad con producción | `docker-compose.dev.yml` |
| **Railway** | Producción | `Dockerfile` + variables de entorno |

---

## Modo 1: Local sin Docker (Recomendado para desarrollo)

### Requisitos
- Nginx instalado en tu sistema
- Backend corriendo en `localhost:8000`
- Frontend (Vite) corriendo en `localhost:5173`

### Cómo funciona

```
nginx.conf                    default.conf
    │                              │
    ├─ Define upstreams:           ├─ Define rutas:
    │   frontend_dev → :5173       │   /api/* → backend_api
    │   backend_api  → :8000       │   /*     → frontend_dev
    │                              │
    └─ include default.conf ───────┘
```

### Comandos

```bash
cd gateway

just start    # Iniciar gateway
just test     # Verificar configuración
just stop     # Detener gateway
just reload   # Recargar configuración (sin reiniciar)
just restart  # Reiniciar (stop + start)
just status   # Ver si está corriendo
just logs     # Ver access logs
just errors   # Ver error logs
```

### Acceso
- App completa: http://localhost:3001
- API directa: http://localhost:3001/api/health

---

## Modo 2: Local con Docker (Paridad con producción)

### Requisitos
- Docker y Docker Compose instalados
- Backend corriendo en `localhost:8000`
- Frontend (Vite) corriendo en `localhost:5173`

### Cómo funciona

```
docker-compose.dev.yml
        │
        ├─ Construye imagen desde gateway/Dockerfile
        │
        ├─ Variables de entorno:
        │   PORT=3001
        │   FRONTEND_UPSTREAM=http://host.docker.internal:5173
        │   BACKEND_UPSTREAM=http://host.docker.internal:8000
        │
        └─ docker-entrypoint.sh
              │
              ├─ Extrae resolvers DNS de /etc/resolv.conf
              ├─ Renderiza nginx.railway.conf.template → default.conf
              └─ Inicia nginx
```

**Nota importante:** `host.docker.internal` es una dirección especial que 
Docker resuelve a tu máquina host, permitiendo que el contenedor 
se comunique con servicios corriendo fuera de Docker.

### Comandos

```bash
cd gateway

just docker-up      # Iniciar gateway con Docker
just docker-up-d    # Iniciar en background
just docker-logs    # Ver logs
just docker-down    # Detener
```

O manualmente:

```bash
cd gateway
docker compose -f docker-compose.dev.yml up --build
docker compose -f docker-compose.dev.yml build --no-cache  # Reconstruir imagen
```

### Acceso
- App completa: http://localhost:3001
- API directa: http://localhost:3001/api/health

---

## Modo 3: Railway (Producción)

En Railway, el gateway se despliega automáticamente usando el `Dockerfile`.
Las variables de entorno se configuran en el dashboard de Railway:

| Variable | Descripción |
|----------|-------------|
| `PORT` | Puerto asignado por Railway |
| `FRONTEND_UPSTREAM` | URL del servicio frontend (ej: `http://frontend.railway.internal`) |
| `BACKEND_UPSTREAM` | URL del servicio backend (ej: `http://backend.railway.internal`) |

---

## Estructura de Archivos

```
gateway/
├── Justfile                      # Comandos just para desarrollo
├── docker-compose.dev.yml        # Docker Compose para desarrollo local
├── Dockerfile                    # Imagen para Railway/Docker
├── docker-entrypoint.sh          # Script de inicio para Docker
├── nginx.conf                    # Config principal (desarrollo local sin Docker)
├── default.conf                  # Rutas para desarrollo local
├── nginx.railway.conf.template   # Template para Railway/Docker
├── logs/                         # Logs de nginx (desarrollo local)
└── temp/                         # Archivos temporales de nginx
```

---

## Troubleshooting

### Error: "Connection refused" en Docker

El contenedor no puede alcanzar tus servicios locales.

**Solución:** Verifica que backend y frontend estén corriendo y que uses 
`host.docker.internal` en las variables de entorno.

### Error: "Could not determine DNS resolver"

El script no pudo extraer nameservers de `/etc/resolv.conf`.

**Solución:** Esto es raro en Docker. Verifica que tu imagen base 
tenga un `/etc/resolv.conf` válido.

### HMR (Hot Module Replacement) no funciona

Vite necesita WebSockets para HMR.

**Verificar:** La configuración de `default.conf` ya incluye soporte 
para WebSocket con `Upgrade` y `Connection` headers.

### Linux: host.docker.internal no funciona

En versiones antiguas de Docker en Linux, esta dirección no existe.

**Solución 1:** Actualiza Docker a 20.10+ (el compose ya incluye `extra_hosts`).

**Solución 2:** Usa `--network host`:
```bash
docker run --network host \
  -e PORT=3001 \
  -e FRONTEND_UPSTREAM=http://127.0.0.1:5173 \
  -e BACKEND_UPSTREAM=http://127.0.0.1:8000 \
  gateway
```

