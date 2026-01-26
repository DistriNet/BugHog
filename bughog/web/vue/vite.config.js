import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    exclude: ['oh-vue-icons/icons']
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
