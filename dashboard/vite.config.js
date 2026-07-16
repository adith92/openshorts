import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendTarget = process.env.VITE_DEV_BACKEND_URL || 'http://127.0.0.1:8000'
const rendererTarget = process.env.VITE_DEV_RENDERER_URL || 'http://127.0.0.1:3100'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/videos': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/thumbnails': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/gallery': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/video': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/render': {
        target: rendererTarget,
        changeOrigin: true,
      },
    },
  },
})
