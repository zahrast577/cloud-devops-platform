import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En développement (npm run dev), les appels /api sont redirigés vers l'API locale.
// En production, c'est nginx qui joue ce rôle (voir nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
