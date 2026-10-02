// Un API de mentira para las pruebas. Los viajes son el ejemplo del contrato
// (docs/ejemplos/respuesta_ilustrativa.json), una respuesta real del motor: si el contrato
// cambia y el ejemplo se regenera, estas pruebas corren contra la forma nueva.

import { vi } from "vitest";
import ejemplo from "../../../docs/ejemplos/respuesta_ilustrativa.json";
import type { Estacionalidad, Eventos, Opciones, PoloDetalle, Recurso, Respuesta } from "../api/tipos";
import { olvidarPedidos } from "../estado/pedido";

export const RESPUESTA = ejemplo as unknown as Respuesta;
export const VERSION = RESPUESTA.version_datos;

export const OPCIONES: Opciones = {
  version_contrato: RESPUESTA.version_contrato,
  version_datos: VERSION,
  origenes: [
    { id: "lima", nombre: "Lima", region: "Lima" },
    { id: "cusco", nombre: "Cusco", region: "Cusco" },
    { id: "puerto-maldonado", nombre: "Puerto Maldonado", region: "Madre de Dios" },
  ],
  intereses: [
    { id: "naturaleza", etiqueta: "Naturaleza", paradas: 2562 },
    { id: "historia", etiqueta: "Historia y arqueología", paradas: 956 },
    { id: "playa", etiqueta: "Playa", paradas: 214 },
  ],
  dias: { minimo: 1, maximo: 14, defecto: 6 },
  presupuesto: { minimo: 100, maximo: 50000, defecto: null },
  altitud_max: { minimo: 0, maximo: 6000, defecto: null },
};

const PRIMERA = RESPUESTA.rutas[0];
if (!PRIMERA) throw new Error("El ejemplo del contrato no trae rutas.");

function recursosDe(ruta: Respuesta["rutas"][number]): Recurso[] {
  return ruta.dias.flatMap((dia) => (dia.paradas ?? []).map((parada) => parada.recurso));
}

const VEREDICTOS: Estacionalidad["veredicto"][] = ["desaconsejado", "advertencia", "viable"];

/** La ficha del polo de la primera ruta, con doce meses de clima inventados para la prueba. */
export const POLO: PoloDetalle = {
  version_contrato: RESPUESTA.version_contrato,
  version_datos: VERSION,
  polo: PRIMERA.polo,
  recursos: recursosDe(PRIMERA),
  clima: Array.from({ length: 12 }, (_, i) => {
    const veredicto = VEREDICTOS[Math.min(2, Math.floor(i / 2))] ?? "viable";
    return {
      mes: i + 1,
      veredicto,
      lluvia_mm: 240 - i * 20,
      explicacion: `Explicación del mes ${i + 1}.`,
      mejores_meses: [7, 8, 9],
    };
  }),
  eventos: PRIMERA.eventos ?? [],
  atribucion: RESPUESTA.atribucion,
};

export const EVENTOS: Eventos = {
  version_contrato: RESPUESTA.version_contrato,
  version_datos: VERSION,
  desde: "2027-07-01",
  hasta: "2027-07-31",
  eventos: RESPUESTA.rutas.flatMap((ruta) => ruta.eventos ?? []),
};

interface Contestacion {
  estado?: number;
  cuerpo: unknown;
}
type Contestar = (url: URL) => Contestacion;

/** La consulta de una URL, con los valores por defecto del contrato: lo que el motor devuelve en `consulta`. */
export function consultaDe(url: URL): Respuesta["consulta"] {
  const p = url.searchParams;
  const numero = (campo: string) => (p.has(campo) ? Number(p.get(campo)) : null);
  const fecha = p.get("fecha_inicio");
  return {
    origen: p.get("origen") ?? "lima",
    mes: fecha ? Number(fecha.slice(5, 7)) : numero("mes"),
    fecha_inicio: fecha,
    dias: numero("dias") ?? 6,
    intereses: p.getAll("intereses") as Respuesta["consulta"]["intereses"],
    presupuesto: numero("presupuesto"),
    altitud_max: numero("altitud_max"),
    sorpresa: p.get("sorpresa") === "true",
  };
}

/** Los viajes del ejemplo, con la consulta que se pidió: el motor siempre la devuelve. */
export function viajesPara(url: URL): Respuesta {
  return { ...RESPUESTA, consulta: consultaDe(url) };
}

const POR_DEFECTO: Record<string, Contestar> = {
  "/v1/opciones": () => ({ cuerpo: OPCIONES }),
  "/v1/viajes": (url) => ({ cuerpo: viajesPara(url) }),
  [`/v1/polos/${POLO.polo.id}`]: () => ({ cuerpo: POLO }),
  "/v1/eventos": () => ({ cuerpo: EVENTOS }),
};

/**
 * Reemplaza `fetch` por un API de mentira. `rutas` cambia lo que contesta cada ruta: un
 * cuerpo fijo o una función de la URL. Devuelve el `fetch` falso, para ver qué se pidió.
 */
export function ponerApi(rutas: Record<string, Contestar | Contestacion> = {}) {
  olvidarPedidos(); // lo que respondió el API anterior no vale para este
  const tabla: Record<string, Contestar | Contestacion> = { ...POR_DEFECTO, ...rutas };
  const falso = vi.fn(async (entrada: RequestInfo | URL): Promise<Response> => {
    const url = new URL(String(entrada));
    const contestar = tabla[url.pathname];
    if (!contestar) return new Response(JSON.stringify({ detail: "No existe." }), { status: 404 });
    const { estado = 200, cuerpo } = typeof contestar === "function" ? contestar(url) : contestar;
    return new Response(JSON.stringify(cuerpo), {
      status: estado,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", falso);
  return falso;
}

/** Lo que se pidió a una ruta del API, como «ruta?parámetros», en orden. */
export function pedidosA(falso: ReturnType<typeof ponerApi>, ruta: string): string[] {
  return falso.mock.calls
    .map(([entrada]) => new URL(String(entrada)))
    .filter((url) => url.pathname === ruta)
    .map((url) => `${url.pathname}${url.search}`);
}

/** Abre la app en una dirección, como si se hubiera escrito en la barra del navegador. */
export function irA(direccion: string): void {
  window.history.replaceState(null, "", direccion);
}
