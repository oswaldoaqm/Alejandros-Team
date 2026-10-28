// El título de la pestaña, que también es lo primero que dice un lector de pantalla al cambiar de pantalla.

import { useEffect } from "react";

const MARCA = "DreemGO";
const POR_DEFECTO = `${MARCA} · Tres viajes por el Perú, día por día`;

export function useTitulo(titulo: string | null): void {
  useEffect(() => {
    document.title = titulo ? `${titulo} · ${MARCA}` : POR_DEFECTO;
  }, [titulo]);
}
