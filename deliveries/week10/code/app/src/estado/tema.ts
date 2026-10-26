// Manejo del tema claro / oscuro de la aplicación.
// Por defecto siempre está activo el modo claro, salvo que la persona decida cambiarlo.

import { useEffect, useState } from "react";

export type Tema = "light" | "dark";

export const CLAVE_TEMA = "dreemgo-tema";

export function obtenerTemaInicial(): Tema {
  if (typeof window === "undefined") return "light";
  try {
    const guardado = localStorage.getItem(CLAVE_TEMA);
    if (guardado === "dark") return "dark";
  } catch {
    // Si localStorage está bloqueado o inaccesible
  }
  // Por defecto siempre modo claro
  return "light";
}

export function useTema(): [Tema, () => void] {
  const [tema, ponerTema] = useState<Tema>(obtenerTemaInicial);

  useEffect(() => {
    document.documentElement.setAttribute("data-tema", tema);
    try {
      localStorage.setItem(CLAVE_TEMA, tema);
    } catch {
      // ignorar fallos de almacenamiento
    }
  }, [tema]);

  const alternar = () => {
    ponerTema((actual) => (actual === "light" ? "dark" : "light"));
  };

  return [tema, alternar];
}
