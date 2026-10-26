import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
const phone = Boolean(process.env.MATCHOS_PHONE_ADDRESS);
const proxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    bypass(req, res) {
      // Phone preview must not expose loopback-only draft diagnostics through its proxy.
      let pathname;
      try {
        pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      } catch {
        res.statusCode = 400;
        res.end('Invalid path');
        return false;
      }
      if (phone && (pathname === '/api/development' || pathname.startsWith('/api/development/'))) {
        res.statusCode = 404;
        res.end('Not found');
        return false;
      }
    },
  },
};
export default defineConfig({
  server: { proxy },
  preview: { proxy },
  build: {
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        testing: fileURLToPath(new URL('./testing.html', import.meta.url)),
      },
    },
  },
});
