import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// En Docker, BACKEND_TARGET=http://backend:5000
// En local, por defecto apunta a localhost:5000
const BACKEND_TARGET = process.env.BACKEND_TARGET || "http://localhost:5000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      // Todas las llamadas /api/* y /admin/* se redirigen al backend Flask
      "/api": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
      "/admin": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
      // El stream MJPEG de la camara tambien pasa por el proxy
      "/video_feed": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
    },
  },
});
