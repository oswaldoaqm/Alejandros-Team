// Preparación de las pruebas (vitest): cada una empieza en la portada, con el almacén vacío
// y el título en blanco. jsdom no desplaza la página: esas funciones se dejan anotando.
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

// jsdom tiene <dialog> pero no sabe abrirlo ni cerrarlo: lo mínimo para que las hojas
// (piezas/Hoja.tsx) se abran, se cierren y avisen que se cerraron, como en un navegador.
const Dialogo = globalThis.HTMLDialogElement;
if (Dialogo && typeof Dialogo.prototype.showModal !== "function") {
  Object.defineProperty(Dialogo.prototype, "open", {
    configurable: true,
    get(this: HTMLDialogElement) {
      return this.hasAttribute("open");
    },
    set(this: HTMLDialogElement, abierto: boolean) {
      this.toggleAttribute("open", abierto);
    },
  });
  Dialogo.prototype.showModal = function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  Dialogo.prototype.close = function (this: HTMLDialogElement) {
    if (!this.hasAttribute("open")) return;
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
}

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
