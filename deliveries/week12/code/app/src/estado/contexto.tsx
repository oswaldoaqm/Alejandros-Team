// Lo que casi todas las pantallas necesitan: cómo navegar y las opciones del formulario
// (orígenes, intereses y rangos), que vienen de GET /v1/opciones.

import { createContext, useContext } from "react";
import type { Opciones } from "../api/tipos";
import type { Nombres } from "../consulta";
import type { Navegar } from "./navegacion";
import type { Pedido } from "./pedido";

export interface Contexto {
  navegar: Navegar;
  opciones: Pedido<Opciones>;
  nombres: Nombres;
}

export const ContextoApp = createContext<Contexto | null>(null);

export function useApp(): Contexto {
  const contexto = useContext(ContextoApp);
  if (!contexto) throw new Error("Falta el contexto de la app.");
  return contexto;
}

/** Los nombres de orígenes e intereses por su identificador, para escribir la consulta. */
export function nombresDe(opciones: Opciones | null): Nombres {
  return {
    origenes: Object.fromEntries((opciones?.origenes ?? []).map((o) => [o.id, o.nombre])),
    intereses: Object.fromEntries((opciones?.intereses ?? []).map((i) => [i.id, i.etiqueta])),
  };
}
