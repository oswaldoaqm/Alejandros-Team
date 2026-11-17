import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { type Contexto, ContextoApp } from "../estado/contexto";
import { Enlace } from "./Enlace";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState(null, "", "/");
});

function mostrar(navegar: Contexto["navegar"]) {
  render(
    <ContextoApp.Provider
      value={{ navegar, opciones: null as never, nombres: { origenes: {}, intereses: {} } }}
    >
      <Enlace href="./?mes=7" volver>
        Tus viajes
      </Enlace>
    </ContextoApp.Provider>,
  );
}

it("Tus viajes abre la lista cuando la pantalla previa no era esa lista", () => {
  window.history.replaceState({ dreemgo: true, desde: `${window.location.origin}/` }, "", "/?mes=7#/ruta/1");
  const navegar = vi.fn();
  const retroceder = vi.spyOn(window.history, "back").mockImplementation(() => {});
  mostrar(navegar);

  fireEvent.click(screen.getByRole("link", { name: "Tus viajes" }));

  expect(navegar).toHaveBeenCalledWith("./?mes=7", { reemplazar: undefined, conservarPosicion: undefined });
  expect(retroceder).not.toHaveBeenCalled();
});

it("Tus viajes retrocede si la pantalla previa era la lista", () => {
  window.history.replaceState(
    { dreemgo: true, desde: `${window.location.origin}/?mes=7` },
    "",
    "/?mes=7#/ruta/1",
  );
  const navegar = vi.fn();
  const retroceder = vi.spyOn(window.history, "back").mockImplementation(() => {});
  mostrar(navegar);

  fireEvent.click(screen.getByRole("link", { name: "Tus viajes" }));

  expect(retroceder).toHaveBeenCalledOnce();
  expect(navegar).not.toHaveBeenCalled();
});
