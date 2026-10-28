import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// La base es relativa: el mismo build sirve en GitHub Pages (/Alejandros-Team/), en otro
// host o en una carpeta cualquiera. La consulta viaja en la URL, no en la ruta.
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    target: "es2022",
    // El mapa (MapLibre) va en su propio archivo y solo se baja cuando se abre.
    chunkSizeWarningLimit: 1100,
  },
  server: { port: 5173, strictPort: true },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/pruebas/preparar.ts"],
  },
});
