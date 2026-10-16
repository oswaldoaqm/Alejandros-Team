// La lista de zonas (public/destinos.json), pedida una sola vez y solo cuando una pantalla la
// necesita: al buscar a dónde ir o para nombrar la zona elegida. Si no llega, el viaje se pide
// igual; solo falta el nombre de la zona.

import { useEffect, useState } from "react";
import type { Destinos } from "../destinos";

let pedido: Promise<Destinos | null> | null = null;

/** Olvida la lista: las pruebas la cambian de una a otra. */
export function olvidarDestinos(): void {
  pedido = null;
}

function cargarDestinos(): Promise<Destinos | null> {
  pedido ??= fetch(new URL("destinos.json", document.baseURI).href)
    .then((r) => (r.ok ? (r.json() as Promise<Destinos>) : null))
    .then((lista) => (lista && Array.isArray(lista.zonas) ? lista : null))
    .catch(() => null)
    .then((lista) => {
      if (lista === null) pedido = null; // la próxima vez se vuelve a pedir
      return lista;
    });
  return pedido;
}

/**
 * La lista; undefined mientras llega (o si `pedir` es false: entonces ni se pide) y null si no
 * llegó.
 */
export function useDestinos(pedir = true): Destinos | null | undefined {
  const [destinos, ponerDestinos] = useState<Destinos | null | undefined>(undefined);
  useEffect(() => {
    if (!pedir) return;
    let vigente = true;
    cargarDestinos().then((lista) => {
      if (vigente) ponerDestinos(lista);
    });
    return () => {
      vigente = false;
    };
  }, [pedir]);
  return pedir ? destinos : undefined;
}
