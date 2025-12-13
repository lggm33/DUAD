import { defineConfig } from 'vite'

// Vite blocks unknown Host headers to mitigate DNS rebinding attacks.
// Railway exposes your app under a *.up.railway.app domain, so we must allow it for `vite preview`.
export default defineConfig({
  server: {
    // Allows `vite dev` to be accessed via Railway-like domains if needed.
    allowedHosts: ['.up.railway.app'],
  },
  preview: {
    // Allows `vite preview` to respond when accessed through Railway's public URL.
    allowedHosts: ['.up.railway.app'],
  },
})


