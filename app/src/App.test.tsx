import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { App } from "./App";
import { irA, ponerApi } from "./pruebas/api";

// Una pantalla con un error de programación: la de «Cómo funciona», solo en esta prueba.
vi.mock("./vistas/Acerca", () => ({
  Acerca: () => {
    throw new Error("falla de prueba");
  },
}));

it("si una pantalla falla, el marco sigue en pie y las demás siguen andando", async () => {
  const errores = vi.spyOn(console, "error").mockImplementation(() => {});
  const avisos = vi.spyOn(console, "warn").mockImplementation(() => {});
  irA("/#/acerca");
  ponerApi();
  render(<App />);

  expect(screen.getByRole("heading", { level: 1, name: "Algo falló en esta pantalla" })).toBeDefined();
  expect(screen.getByRole("link", { name: "Volver al inicio" }).getAttribute("href")).toBe("./");

  await userEvent.click(screen.getByRole("link", { name: "Mis viajes" }));
  expect(screen.getByRole("heading", { level: 1, name: "Mis viajes" })).toBeDefined();
  expect(avisos).toHaveBeenCalled();
  errores.mockRestore();
  avisos.mockRestore();
});
