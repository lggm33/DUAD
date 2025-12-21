import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API calls in dev to avoid CORS (frontend:5173 -> backend:8000)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    // Allow Railway hostname when running `vite preview` in production-like environments.
    allowedHosts: ['lyfter-fe-stating.up.railway.app'],
  },
})
