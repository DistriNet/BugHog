import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  optimizeDeps: {
    include: ['oh-vue-icons/icons']
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    https: false,
    cors: false,
    allowedHosts: ['bughog.io'],
  }
})
