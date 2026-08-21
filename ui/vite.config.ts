import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Serve the couponfinder CLI's output folder as static assets, so results.csv
  // is always fetched live from ../files/results.csv (no copy step needed).
  publicDir: fileURLToPath(new URL('../files', import.meta.url)),
})
