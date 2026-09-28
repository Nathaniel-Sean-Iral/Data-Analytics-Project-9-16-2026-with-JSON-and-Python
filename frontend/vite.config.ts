import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import type { ServerResponse } from 'node:http';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Without this, Vite's proxy answers 500 when the API is not running.
        // The API client only treats 0/404/405/501/502/503/504 as "backend
        // unavailable" and falls back to demo data, so a 500 would surface as
        // a login error instead. Report an unreachable upstream as 503 so the
        // demo-data fallback keeps working.
        configure: (proxy) => {
          proxy.on('error', (err, _req, res) => {
            const serverRes = res as ServerResponse;
            if (serverRes.writableEnded) return;
            serverRes.writeHead(503, { 'Content-Type': 'application/json' });
            serverRes.end(JSON.stringify({ detail: `Backend unavailable: ${err.message}` }));
          });
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});