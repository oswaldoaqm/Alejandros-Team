// El tema claro u oscuro de la app. Manda lo que la persona elige con el botón, y queda guardado. Mientras
// no elija, sigue al del sistema, también si lo cambia con la app abierta. El script de index.html hace la
// misma cuenta antes de que cargue la app, para que no parpadee.

import { useEffect, useState } from "react";

export type Tema = "light" | "dark";

/** Lo que la persona eligió con el botón. */
export const CLAVE_TEMA = "dreemgo-tema-elegido";
/**
 * La clave de la versión anterior, que guardaba «light» al abrir, aunque nadie lo hubiera elegido. De ella
 * solo vale «dark», que sí salía del botón.
 */
export const CLAVE_VIEJA = "dreemgo-tema";
const OSCURO = "(prefers-color-scheme: dark)";

/** El tema que la persona eligió, o null si no eligió ninguno (o el navegador no deja leerlo). */
export function temaElegido(): Tema | null {
  try {
    const elegido = localStorage.getItem(CLAVE_TEMA);
    if (elegido === "dark" || elegido === "light") return elegido;
    return localStorage.getItem(CLAVE_VIEJA) === "dark" ? "dark" : null;
  } catch {
    return null;
  }
}

function temaDelSistema(): Tema {
  return window.matchMedia?.(OSCURO).matches ? "dark" : "light";
}

export function obtenerTemaInicial(): Tema {
  if (typeof window === "undefined") return "light";
  return temaElegido() ?? temaDelSistema();
}

function guardar(tema: Tema) {
  try {
    localStorage.setItem(CLAVE_TEMA, tema);
    localStorage.removeItem(CLAVE_VIEJA);
  } catch {
    // Si no se puede guardar, el cambio dura lo que dure la página.
  }
}

export function useTema(): [Tema, () => void] {
  const [tema, ponerTema] = useState<Tema>(obtenerTemaInicial);

  useEffect(() => {
    document.documentElement.setAttribute("data-tema", tema);
  }, [tema]);

  // Si el sistema cambia de tema y la persona no eligió uno, la app cambia con él.
  useEffect(() => {
    const consulta = window.matchMedia?.(OSCURO);
    if (!consulta?.addEventListener) return;
    const alCambiar = () => {
      if (temaElegido() === null) ponerTema(consulta.matches ? "dark" : "light");
    };
    consulta.addEventListener("change", alCambiar);
    return () => consulta.removeEventListener("change", alCambiar);
  }, []);

  const alternar = () => {
    const nuevo: Tema = tema === "light" ? "dark" : "light";
    guardar(nuevo);
    ponerTema(nuevo);
  };

  return [tema, alternar];
}
