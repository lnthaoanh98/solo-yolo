import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  base: "/static/",
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8080",
      "/sample-data": "http://127.0.0.1:8080",
      "/health": "http://127.0.0.1:8080"
    }
  },
  build: {
    outDir: "../app/static",
    emptyOutDir: true,
    sourcemap: false
  }
});
