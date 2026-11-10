import { defineConfig, devices } from "@playwright/test";
import { CLAVE_DE_LA_PRUEBA } from "./e2e/clave";

// Las pruebas de punta a punta corren contra el API de verdad y la app ya construida:
// levantan los dos, o usan los que ya estén corriendo en esta máquina.
const API = "http://localhost:8000";
const APP = "http://localhost:5173";
const enCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "e2e",
  timeout: 45_000,
  expect: { timeout: 15_000 }, // la primera consulta espera a que el API cargue sus datos
  fullyParallel: true,
  forbidOnly: enCI,
  retries: enCI ? 1 : 0,
  reporter: enCI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: APP,
    locale: "es-PE",
    timezoneId: "America/Lima",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "celular", use: { ...devices["Pixel 7"] } },
    { name: "escritorio", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: [
    {
      command: "python -m uvicorn dreemgo.api.app:app --port 8000",
      cwd: "..",
      // Con clave, para que la prueba pueda publicar un evento. Lo publicado queda en memoria.
      env: { DREEMGO_CLAVE_PUBLICADOR: CLAVE_DE_LA_PRUEBA },
      url: `${API}/v1/salud`,
      reuseExistingServer: !enCI,
      timeout: 60_000,
    },
    {
      command: "npm run build && npm run preview",
      url: APP,
      reuseExistingServer: !enCI,
      timeout: 120_000,
    },
  ],
});
