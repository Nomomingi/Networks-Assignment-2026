import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  // Base path for GitHub Pages: https://nomomingi.github.io/Networks-Assignment-2026/
  base: '/Networks-Assignment-2026/',
  plugins: [react()],
  resolve: {
    alias: {
      "@":            path.resolve(__dirname, "./src"),
      "@components":  path.resolve(__dirname, "./src/components"),
      "@pages":       path.resolve(__dirname, "./src/pages"),
      "@assets":      path.resolve(__dirname, "./src/assets"),
    },
  },
  server: {
    // Allow both local and ngrok dev access
    allowedHosts: ['localhost', '.ngrok-free.app'],
  },
})
