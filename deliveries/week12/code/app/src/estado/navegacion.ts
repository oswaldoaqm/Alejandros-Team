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

/** Si a la pantalla actual se llegó desde otra de la app: entonces «volver» es retroceder. */
export function vinoDeLaApp(): boolean {
  const estado: unknown = window.history.state;
  return typeof estado === "object" && estado !== null && "dreemgo" in estado;
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
    else window.history.pushState({ dreemgo: true }, "", destino);
    ponerVista(vistaDe(destino));
    if (!opciones.conservarPosicion) window.scrollTo({ top: 0 });
  }, []);

  return [vista, navegar];
}
