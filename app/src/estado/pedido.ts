// Un pedido al API como estado de React. Mientras llega uno nuevo se conserva lo anterior
// (la pantalla no salta), y lo ya pedido en esta sesión no se vuelve a pedir: el motor es
// determinista para una misma versión de datos.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ErrorApi, pedir } from "../api/cliente";

export interface Pedido<T> {
  datos: T | null;
  error: ErrorApi | null;
  cargando: boolean;
  /** La clave del pedido al que corresponden `datos`. */
  de: string | null;
  reintentar: () => void;
}

const memoria = new Map<string, unknown>();

/** Para las pruebas: olvida lo pedido. */
export function olvidarPedidos(): void {
  memoria.clear();
}

/** Pide `ruta?parametros`. Con `ruta` en null no pide nada. */
export function usePedido<T>(ruta: string | null, parametros = ""): Pedido<T> {
  const llave = ruta === null ? null : `${ruta}?${parametros}`;
  const [intento, ponerIntento] = useState(0);
  const [estado, ponerEstado] = useState<Omit<Pedido<T>, "reintentar">>(() => {
    const guardado = llave ? (memoria.get(llave) as T | undefined) : undefined;
    return {
      datos: guardado ?? null,
      error: null,
      cargando: llave !== null && guardado === undefined,
      de: llave,
    };
  });
  const ultimoIntento = useRef(0);

  useEffect(() => {
    if (llave === null || ruta === null) {
      ponerEstado({ datos: null, error: null, cargando: false, de: null });
      return;
    }
    const forzar = intento !== ultimoIntento.current;
    ultimoIntento.current = intento;
    const guardado = memoria.get(llave) as T | undefined;
    if (guardado !== undefined && !forzar) {
      ponerEstado({ datos: guardado, error: null, cargando: false, de: llave });
      return;
    }
    const control = new AbortController();
    ponerEstado((antes) => ({ ...antes, error: null, cargando: true }));
    pedir<T>(ruta, { parametros: new URLSearchParams(parametros), senal: control.signal })
      .then((datos) => {
        memoria.set(llave, datos);
        ponerEstado({ datos, error: null, cargando: false, de: llave });
      })
      .catch((causa: unknown) => {
        if (control.signal.aborted) return;
        const error =
          causa instanceof ErrorApi ? causa : new ErrorApi("servidor", "Algo falló al leer la respuesta.");
        ponerEstado({ datos: null, error, cargando: false, de: llave });
      });
    return () => control.abort();
  }, [llave, ruta, parametros, intento]);

  const reintentar = useCallback(() => ponerIntento((n) => n + 1), []);
  return useMemo(() => ({ ...estado, reintentar }), [estado, reintentar]);
}
