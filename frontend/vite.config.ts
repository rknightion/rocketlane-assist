import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Generate source maps for production builds
    sourcemap: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // Use backend service name when running in Docker
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
