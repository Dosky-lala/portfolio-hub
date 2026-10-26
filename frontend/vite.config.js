import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Dev only: forward /api to the FastAPI server, like Nginx will in production
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
