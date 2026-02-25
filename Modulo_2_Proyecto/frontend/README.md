# Vanilla JS + Vite

This project uses **Vanilla JavaScript** with **Vite** as the build tool.

## Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview

# Lint code
pnpm lint
```

## Project Structure

```
src/
├── main.js                    # Application entry point
├── infrastructure/
│   └── api/
│       ├── http.js           # HTTP client utilities
│       └── health.js         # Health check API calls
└── styles/
    ├── index.css             # Global styles
    └── app.css               # Application-specific styles
```

## Railway Deployment

This project is configured for deployment on Railway:

- Uses **nginx** to serve static files in production
- The `Dockerfile` builds the project with Vite and serves via nginx
- API calls are proxied through the gateway

## API Proxy (Development)

During development, API calls to `/api` are proxied to `http://localhost:8000` to avoid CORS issues. This is configured in `vite.config.js`.
