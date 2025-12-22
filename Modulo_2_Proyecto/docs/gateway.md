# Gateway (Local + Railway) para mismo origin (sin CORS) con Frontend/Backend separados

## Objetivo

Unificar la experiencia **dev** y **prod** para que el navegador siempre vea **un solo origen**:

- `/` y assets → Frontend
- `/api/*` → Backend

Esto elimina CORS y hace que las **cookies de refresh token** funcionen como **first‑party** (evitando `SameSite=None` y problemas de third‑party cookies).

---

## Arquitectura (alto nivel)

### Local (opción 2: gateway delante de Vite dev + backend)

**Browser** → `http://localhost:<GATEWAY_PORT>`

- Si `path` empieza con `/api`:
  - Gateway → `http://localhost:8000/api/...` (Backend)
- Si no:
  - Gateway → `http://localhost:5173/...` (Vite dev server, HMR)

### Railway (gateway público + servicios internos)

**Browser** → `https://<gateway-public-domain>`

- Si `path` empieza con `/api`:
  - Gateway → `http://<backend-service>.railway.internal:<BACKEND_PORT>/api/...`
- Si no:
  - Gateway → `http://<frontend-service>.railway.internal:<FRONTEND_PORT>/...` (o servir estáticos desde el gateway si prefieres)

**Nota clave (Railway):** el private network es **solo server-to-server**. El navegador no puede resolver `railway.internal`. El gateway sí puede. Referencia: [Railway Private Networking](https://docs.railway.com/guides/private-networking)

---

## Decisiones recomendadas (para tu auth: JWT + refresh cookie)

- **Refresh token en cookie HttpOnly**: mantener `Secure=true` y preferir `SameSite=Lax`.
- **Mismo origin** (gateway): evita CORS y reduce fricción con cookies.
- **Backend sin dominio público (opcional)**: más seguro; el gateway lo consume por private network.

---

## Gateway local (opción 2) — Pasos atómicos

> La idea es correr **3 procesos**: Backend (8000), Frontend (5173) y Gateway (por ejemplo 3001).

### 1) Elegir tecnología de gateway

Recomendación: **Caddy** o **Nginx** (reverse proxy + soporte de WebSockets).

- Caddy: config simple, buena DX
- Nginx: estándar, muy robusto

*(No es obligatorio usar la misma tecnología en local y Railway, pero ayuda a mantener paridad.)*

### 2) Definir puertos locales

- `FRONTEND_DEV_PORT = 5173`
- `BACKEND_PORT = 8000`
- `GATEWAY_PORT = 3001` (o el que prefieras)

### 3) Configurar rutas en el gateway (pseudocódigo)

Reglas:

- **Rule A**: si `request.path` comienza con `/api` → upstream = backend
- **Rule B**: si no → upstream = frontend

Pseudocódigo:

```
if path startsWith "/api":
  proxy_pass "http://localhost:8000"
else:
  proxy_pass "http://localhost:5173"
```

**Importante para HMR**: el proxy debe soportar **WebSockets** (Vite HMR usa WS).

### 4) Levantar los servicios

- Iniciar backend en `:8000`
- Iniciar Vite dev server en `:5173`
- Iniciar gateway en `:3001`

Validaciones rápidas:

- Navegador abre `http://localhost:3001/` (sirve frontend)
- `GET http://localhost:3001/api/v1/health` (llega al backend)
- Login/refresh: el navegador ve cookies como first‑party y ya no dependes de CORS

### 5) Buenas prácticas (local)

- Mantén en el frontend **solo rutas relativas** (ej: `/api/v1/...`) para no “hardcodear” dominios.
- Si en algún momento necesitas HTTPS local para probar `Secure` cookies, usa un certificado local (mkcert) y configura el gateway para TLS (opcional).

---

## Nginx gateway (local + Railway) — Pasos para “cero conocimiento”

Esta sección aterriza el gateway usando **Nginx** porque es un reverse proxy estándar y muy estable.

### 0) Instalar Nginx en local

Elige tu OS:

#### macOS (recomendado: Homebrew)

- Instalar:
  - `brew install nginx`
- Verificar:
  - `nginx -v`

#### Ubuntu/Debian

- Instalar:
  - `sudo apt update`
  - `sudo apt install nginx`
- Verificar:
  - `nginx -v`

#### Alternativa (recomendada si quieres evitar instalaciones): Docker

Si prefieres no “ensuciar” tu máquina, usa un contenedor de Nginx:

- Ventaja: mismo enfoque que Railway (normalmente Docker)
- Desventaja: necesitas Docker corriendo

---

### A) Gateway con Nginx en local (opción 2, manteniendo HMR)

**Meta:** abrir `http://localhost:<GATEWAY_PORT>` y que:

- `/api/*` → `http://localhost:8000`
- `/*` → `http://localhost:5173` (Vite dev + HMR)

#### A.1) Crear carpeta del gateway

- En la raíz del repo crea una carpeta: `gateway/`

Estructura recomendada:

- `gateway/`
  - `nginx.conf` (config base)
  - `default.conf` (rutas y proxy rules)

#### A.1.1) Cómo hacer que Nginx lea la config desde `gateway/`

Nginx puede arrancar usando una config **en cualquier carpeta**, sin tocar la instalación global.

Concepto:

- `-c` apunta al archivo `nginx.conf`
- `-p` define el “prefix” (desde donde Nginx resuelve rutas relativas como `logs/`, `temp/`, etc.)

Pseudocomando:

```
nginx -p "<ruta-al-repo>/gateway" -c "<ruta-al-repo>/gateway/nginx.conf"
```

Detener:

```
nginx -p "<ruta-al-repo>/gateway" -c "<ruta-al-repo>/gateway/nginx.conf" -s stop
```

**Tip:** Esto es ideal para local porque no dependes de `/etc/nginx/*`.

#### A.2) Definir puertos (decisión)

- `GATEWAY_PORT`: por ejemplo `3001`
- `FRONTEND_DEV_PORT`: `5173`
- `BACKEND_PORT`: `8000`

#### A.3) Configurar el enrutamiento en Nginx (pseudocódigo)

Reglas dentro del `server`:

```
listen GATEWAY_PORT

location "/api/":
  proxy_pass "http://localhost:BACKEND_PORT/"

location "/":
  proxy_pass "http://localhost:FRONTEND_DEV_PORT/"
  support_websockets = true
```

**Detalle importante (HMR):** Vite necesita WebSockets. En Nginx esto se resuelve reenviando `Upgrade`/`Connection` en el location que apunta al frontend.

#### A.4) Ejecutar el gateway local

Opciones para correr Nginx localmente:

- **Opción 1 (Nginx instalado)**:
  - Asegúrate de que `gateway/nginx.conf` incluya tu `default.conf`
  - Arranca Nginx usando `-p` y `-c` (ver A.1.1)
- **Opción 2 (Docker recomendado)**:
  - Correr un contenedor de Nginx montando tus configs de `gateway/`
  - Mapear el `GATEWAY_PORT` del host al puerto interno de Nginx
  - Nota: en local puedes fijar el puerto interno del contenedor a `3001` sin variables

Validación:

- Abrir `http://localhost:<GATEWAY_PORT>/` (debe cargar frontend)
- Probar `http://localhost:<GATEWAY_PORT>/api/v1/health` (debe responder backend)

---

### B) Gateway con Nginx en Railway (un solo dominio público)

**Meta:** el navegador solo conoce el dominio del gateway, y el gateway habla con FE/BE por private network.

#### B.0) Por qué en Railway casi siempre conviene Docker para Nginx

Nginx no es una “app Node” o “app Python”; lo más directo en Railway es desplegarlo como:

- **Imagen Docker** que incluya:
  - Nginx
  - Tu config (en `gateway/`)
  - Un paso de “templating” para usar el `$PORT` que Railway inyecta

#### B.0.1) Punto crítico: `listen $PORT`

Railway asigna el puerto público vía variable de entorno `PORT`.

Nginx **no** interpreta variables de entorno dentro del `.conf` “tal cual”.
Por eso, en Docker normalmente se hace:

- Guardas una plantilla `nginx.conf.template` con `${PORT}`
- Al iniciar el contenedor, ejecutas `envsubst` para generar `nginx.conf` real
- Arrancas Nginx con ese archivo generado

(Esto evita hardcodear el puerto.)

#### B.1) Crear un tercer servicio en Railway: `gateway`

- Crea el servicio `gateway` en el mismo proyecto/environment que FE y BE.
- Dale **dominio público** al gateway.
- (Recomendado) Quita dominio público a backend si solo lo consumirá el gateway.

#### B.2) Variables (concepto)

En el servicio `gateway` define variables para apuntar a tus upstreams internos:

- `FRONTEND_UPSTREAM = http://<frontend-service>.railway.internal:<FRONTEND_INTERNAL_PORT>`
- `BACKEND_UPSTREAM = http://<backend-service>.railway.internal:<BACKEND_INTERNAL_PORT>`

Referencia: el hostname `railway.internal` funciona solo **entre servicios** dentro de Railway ([Private Networking](https://docs.railway.com/guides/private-networking)).

#### B.3) Puertos internos estables (decisión crítica)

Para que Nginx sepa a qué puerto llamar en `railway.internal`, necesitas que FE/BE expongan un puerto estable para tráfico interno.

Pseudodecisión:

- Frontend interno en `5173` (o `3000`)
- Backend interno en `8000`

*(Esto suele implicar ajustar comandos de arranque en Railway para escuchar en esos puertos de forma consistente.)*

#### B.4) Configuración de rutas en Nginx (pseudocódigo)

Reglas:

```
listen $PORT  // el puerto público que Railway inyecta al gateway

location "/api/":
  proxy_pass BACKEND_UPSTREAM

location "/":
  proxy_pass FRONTEND_UPSTREAM
```

#### B.5) Deploy

Dos caminos comunes:

- **Gateway como servicio Docker**: empaquetas Nginx + configs en una imagen.
- **Gateway como servicio “Nixpacks/Start Command”**: menos común para Nginx; normalmente Docker es lo más directo.

Checklist de deploy (Docker, nivel “pasos atómicos”):

- Crear en `gateway/`:
  - un `Dockerfile` que copie tus configs al contenedor
  - una plantilla de config con `${PORT}` y con upstreams vía variables (`FRONTEND_UPSTREAM`, `BACKEND_UPSTREAM`)
  - un script de arranque que:
    - materialice la plantilla (envsubst)
    - arranque Nginx en foreground (para que Railway lo supervise)
- En Railway (servicio `gateway`):
  - setear variables:
    - `FRONTEND_UPSTREAM`
    - `BACKEND_UPSTREAM`
  - build: usando Dockerfile
  - deploy

Validación:

- Abre el dominio del gateway
- Prueba `/` y `/api/v1/health`
- Confirma que login/refresh funciona sin CORS y que la cookie se comporta como first‑party

---

## Railway (3 servicios) — Setup exacto con Dockerfile (gateway + frontend)

### Servicios y exposición pública

- **`gateway`**: único **Public Domain**
- **`frontend`**: **sin** Public Domain (solo privado)
- **`backend`**: **sin** Public Domain (solo privado)

### Archivos que ya existen en este repo

- **Gateway**: `gateway/Dockerfile`, `gateway/nginx.railway.conf.template`, `gateway/docker-entrypoint.sh`
- **Frontend estático**: `frontend/Dockerfile`, `frontend/nginx.conf.template`, `frontend/docker-entrypoint.sh`

### Variables en Railway (pasos atómicos)

#### Backend service

- Setear `PORT` a un valor estable (ej: `8000`)
- Asegurar que el backend escucha en todas las interfaces (Railway recomienda `::`): [Private Networking](https://docs.railway.com/guides/private-networking)

#### Frontend service

- Setear `PORT` a un valor estable (ej: `3000`)

#### Gateway service

- Setear:
  - `FRONTEND_UPSTREAM = http://${{frontend.RAILWAY_PRIVATE_DOMAIN}}:${{frontend.PORT}}`
  - `BACKEND_UPSTREAM = http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}`

### Deploy (orden recomendado)

- Deploy `backend`
- Deploy `frontend`
- Deploy `gateway`

### Validación

- `https://<gateway-domain>/` (debe cargar frontend)
- `https://<gateway-domain>/api/v1/health` (debe responder backend)
  - No CORS (mismo origin)

### Nota: ¿por qué a veces “tengo que reiniciar el gateway” tras redeploy del frontend?

En Railway, cuando redeployas `frontend` o `backend`, el hostname `*.railway.internal` puede apuntar a **nuevas IPs**.
Nginx, por defecto, suele **resolver DNS una vez** y quedarse con esa IP; si el upstream cambia, puedes ver `502/504` hasta reiniciar/recargar.

En este repo, el gateway para Railway ya está preparado para evitarlo:

- Lee el DNS resolver desde `/etc/resolv.conf`
- Configura `resolver ... valid=10s`
- Usa `proxy_pass` con variables, forzando re-resolución en runtime

### Hardening aplicado al gateway (Railway)

- **Ocultar versión**: `server_tokens off`
- **Headers de seguridad**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- **Límites básicos**: `client_max_body_size`, timeouts de body/response
- **Restricción de métodos**:
  - `/api/*`: permite `GET/POST/PUT/PATCH/DELETE/OPTIONS`
  - `/*`: permite `GET/HEAD/OPTIONS`
- **Host header safety**: el gateway no reenvía el `Host` del cliente al upstream; en su lugar extrae el hostname del upstream y lo usa como `Host` hacia FE/BE

---

## Gateway en Railway — Pasos atómicos

### 1) Crear un servicio nuevo: `gateway`

- En tu proyecto Railway, crea un tercer servicio (además de `frontend` y `backend`).
- El gateway será el **único** con dominio público recomendado.

### 2) Networking: decidir qué expones públicamente

Opción recomendada:

- **Gateway**: con dominio público (y si puedes, dominio custom)
- **Backend**: sin dominio público (solo privado)
- **Frontend**: opcional (puede quedar sin dominio si el gateway lo sirve/proxy)

### 3) Asegurar que frontend y backend escuchan en todas las interfaces

Railway recomienda escuchar en `::` (dual stack) cuando sea posible. Referencia: [Railway Private Networking](https://docs.railway.com/guides/private-networking)

### 4) Definir puertos internos estables (punto crítico)

Para que el gateway pueda llamar a `railway.internal` necesita:

- host interno del servicio (ej: `lyfter-be.railway.internal`)
- **puerto** donde ese servicio escucha

Railway aclara que el puerto no se “descubre” automáticamente desde otro servicio; por eso tienes dos rutas:

- **Ruta 1 (recomendada)**: fijar puertos internos estables (ej: frontend 5173/3000, backend 8000) y configurar dominios/variables acorde.
- **Ruta 2**: mantener puertos dinámicos (`$PORT`) y “pasar” el puerto al gateway mediante variables/convención (más frágil).

Pseudodefinición recomendada:

- `FRONTEND_INTERNAL_PORT = 5173` (o 3000)
- `BACKEND_INTERNAL_PORT = 8000`

Y cada servicio debe iniciar escuchando en ese puerto.

### 5) Configurar el gateway para usar private network

En el gateway, define upstreams internos:

- `FRONTEND_UPSTREAM = http://<frontend-service>.railway.internal:<FRONTEND_INTERNAL_PORT>`
- `BACKEND_UPSTREAM = http://<backend-service>.railway.internal:<BACKEND_INTERNAL_PORT>`

Luego aplica la misma regla de rutas:

```
if path startsWith "/api":
  proxy_pass BACKEND_UPSTREAM
else:
  proxy_pass FRONTEND_UPSTREAM
```

### 6) Validación en Railway

- Abre el dominio público del gateway:
  - `/` carga el frontend
  - `/api/v1/health` responde desde backend
- Verifica que:
  - No hay CORS
  - El refresh cookie funciona sin `SameSite=None`

---

## Comparación: Gateway vs Opción C (CORS)

- **Gateway**:
  - Pros: sin CORS, cookies first‑party, menos edge cases, backend puede ser privado
  - Contras: servicio extra (gateway) y algo de config de proxy
- **CORS**:
  - Pros: sin gateway, menos infraestructura
  - Contras: con cookies requiere `SameSite=None; Secure`, `credentials: include`, preflights; más frágil

Referencia del tutorial oficial que usa CORS (Opción C): [Deploying a Monorepo to Railway](https://docs.railway.com/tutorials/deploying-a-monorepo)


