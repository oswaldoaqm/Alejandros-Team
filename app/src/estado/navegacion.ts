// La pantalla actual, leída de la URL, y cómo cambiarla sin recargar la página.

import { useCallback, useEffect, useState } from "react";
import { type Vista, vistaDe } from "../ruta";

export type Navegar = (
  enlace: string,
  opciones?: { reemplazar?: boolean; conservarPosicion?: boolean },
) => void;

function vistaActual(): Vista {
  return vistaDe(new URL(window.location.href));
}

/** Retroceder solo si la pantalla anterior es el destino del enlace «volver». */
export function vinoDeLaApp(enlace: string): boolean {
  const estado: unknown = window.history.state;
  if (typeof estado !== "object" || estado === null || !("dreemgo" in estado) || !("desde" in estado))
    return false;
  if (typeof estado.desde !== "string") return false;
  try {
    const anterior = new URL(estado.desde, window.location.href);
    const destino = new URL(enlace, window.location.href);
    if (anterior.href === destino.href) return true;

    // Una ficha de lugar o el calendario pueden haberse abierto desde un viaje.
    // Ahí «Tus viajes» vuelve al viaje abierto, sin perder el punto de lectura.
    const actual = vistaActual();
    const vistaAnterior = vistaDe(anterior);
    const vistaDestino = vistaDe(destino);
    if (
      (actual.tipo === "polo" || actual.tipo === "calendario") &&
      vistaAnterior.tipo === "resultados" &&
      vistaAnterior.ruta !== null &&
      vistaDestino.tipo === "resultados" &&
      vistaDestino.ruta === null
    ) {
      const consultaAnterior = new URLSearchParams(anterior.search);
      const consultaDestino = new URLSearchParams(destino.search);
      consultaAnterior.delete("v");
      consultaDestino.delete("v");
      return consultaAnterior.toString() === consultaDestino.toString();
    }
    return false;
  } catch {
    return false;
  }
}

export function useNavegacion(): [Vista, Navegar] {
  const [vista, ponerVista] = useState<Vista>(vistaActual);

  useEffect(() => {
    const alCambiar = () => ponerVista(vistaActual());
    window.addEventListener("popstate", alCambiar);
    window.addEventListener("hashchange", alCambiar);
    return () => {
      window.removeEventListener("popstate", alCambiar);
      window.removeEventListener("hashchange", alCambiar);
    };
  }, []);

  const navegar = useCallback<Navegar>((enlace, opciones = {}) => {
    const destino = new URL(enlace, window.location.href);
    if (opciones.reemplazar) window.history.replaceState(window.history.state, "", destino);
    else window.history.pushState({ dreemgo: true, desde: window.location.href }, "", destino);
    ponerVista(vistaDe(destino));
    if (!opciones.conservarPosicion) window.scrollTo({ top: 0 });
  }, []);

  return [vista, navegar];
}
