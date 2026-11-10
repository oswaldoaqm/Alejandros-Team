// La lista de fotos (public/fotos.json), pedida una sola vez y solo cuando una pantalla la usa.
// Si no llega, la app sigue sin fotos: cada viaje muestra su flor.

import { useEffect, useState } from "react";
import type { Fotos } from "../fotos";

let pedido: Promise<Fotos | null> | null = null;

/** Olvida la lista: las pruebas la cambian de una a otra. */
export function olvidarFotos(): void {
  pedido = null;
}

function cargarFotos(): Promise<Fotos | null> {
  pedido ??= fetch(new URL("fotos.json", document.baseURI).href)
    .then((r) => (r.ok ? (r.json() as Promise<Fotos>) : null))
    .then((fotos) =>
      fotos && typeof fotos.lugares === "object" && typeof fotos.bases === "object" ? fotos : null,
    )
    .catch(() => null);
  return pedido;
}

export function useFotos(): Fotos | null {
  const [fotos, ponerFotos] = useState<Fotos | null>(null);
  useEffect(() => {
    let vigente = true;
    cargarFotos().then((lista) => {
      if (vigente) ponerFotos(lista);
    });
    return () => {
      vigente = false;
    };
  }, []);
  return fotos;
}
