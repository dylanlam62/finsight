import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In Docker the backend is reachable via service name; locally it's localhost.
const apiTarget = process.env.API_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
});
