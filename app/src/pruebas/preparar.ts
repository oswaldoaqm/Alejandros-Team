// Preparación de las pruebas (vitest): cada una empieza en la portada, con el almacén vacío
// y el título en blanco. jsdom no desplaza la página: esas funciones se dejan anotando.
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  document.title = "";
  Element.prototype.scrollIntoView = vi.fn();
  window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
});

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
