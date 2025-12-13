## Backend — Lyfter DnD (Módulo 2)

Este backend es parte del proyecto **Lyfter DnD**, una plataforma web para que un grupo de amigos pueda jugar Dungeons & Dragons online con:
- autenticación (JWT)
- roles (Jugador / DM / Admin)
- gestión de partidas, personajes e inventario
- chat en tiempo real y tiradas de dados con reglas de visibilidad

El objetivo principal es **aprender construyendo desde cero** (arquitectura, API, base de datos, caching, auth, tests y deploy).

## Stack (backend)
- **Flask**: servidor HTTP y rutas.
- **PostgreSQL**: base de datos principal.
- **SQLAlchemy**: acceso seguro a datos + queries eficientes (joins/eager loading).
- **Redis**: cache para rendimiento (mínimo 2 objetos cacheados).
- **JWT**: protección de endpoints + datos relevantes en payload.
- **PyTest**: tests de API y tests de lógica.

## Estructura del proyecto (resumen)
Este backend está pensado como un **monolito modular**, organizado por dominios:
- `app/api/`: rutas HTTP (controllers).
- `app/realtime/`: eventos WebSocket (chat/dice).
- `app/domain/`: lógica de negocio (services), acceso a datos (repositories) y modelos (models por entidad).
- `app/extensions/`: inicialización de dependencias (db/redis/jwt).

La referencia completa de la estructura y convenciones se mantiene en Notion (ver enlaces abajo).

## Comandos (Just)
Los comandos de desarrollo están definidos en el `Justfile`.

Pseudoflujo típico:
```text
install deps
run dev server
hit /health
```

## Deploy (Railway/Railpack)
Railpack detecta proyectos Python por `requirements.txt` (entre otros) y detecta Flask si `flask` y `gunicorn` están instalados.

Pseudocomando de arranque esperado:
```text
gunicorn --bind 0.0.0.0:${PORT} main:app
```

## Documentación en Notion (source of truth)
- **Proyecto (home)**: `https://www.notion.so/2c8d3a476b26804ba32de7ce57f642fc`
- **Arquitectura** (diagramas, ADRs, modelo de datos, auth, API contract, realtime, cache, testing, deploy): `https://www.notion.so/2c8d3a476b2680e2b0a9ce02ccd03b53`
- **Tareas / Kanban** (sprints y tareas): `https://www.notion.so/2c8d3a476b26800586f9f2fcd8fdc8a5`

