// Un API de mentira para las pruebas. Los viajes son el ejemplo del contrato
// (docs/ejemplos/respuesta_ilustrativa.json), una respuesta real del motor: si el contrato
// cambia y el ejemplo se regenera, estas pruebas corren contra la forma nueva.

import { vi } from "vitest";
import ejemplo from "../../../docs/ejemplos/respuesta_ilustrativa.json";
import type {
  Estacionalidad,
  Evento,
  Eventos,
  Opciones,
  PoloDetalle,
  Recurso,
  Respuesta,
} from "../api/tipos";
import type { Destinos } from "../destinos";
import { olvidarDestinos } from "../estado/destinos";
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

/**
 * Un evento como los que publican los municipios: el que devuelve POST /v1/eventos. Con un
 * nombre que no se confunda con ninguno del ejemplo del contrato.
 */
export const PUBLICADO: Evento = {
  id: "p-0123456789ab",
  nombre: "Feria de Productores",
  tipo: "Feria gastronómica",
  fecha_inicio: "2026-11-13",
  fecha_fin: "2026-11-15",
  precision_fecha: "exacta",
  distrito: "Villa Rica",
  provincia: "Oxapampa",
  region: "Pasco",
  fuente: "publicado",
  publicado_por: "Municipalidad Distrital de Villa Rica",
  url: "https://www.munivillarica.gob.pe/festival",
};

interface Contestacion {
  estado?: number;
  cuerpo: unknown;
}
/** Lo que el falso API sabe de un pedido además de su URL. */
export interface PedidoRecibido {
  metodo: string;
  cabeceras: Headers;
  /** El cuerpo, ya leído como JSON; undefined si el pedido no trae. */
  cuerpo: unknown;
}
type Contestar = (url: URL, pedido: PedidoRecibido) => Contestacion;

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
    solo_por_tierra: p.get("solo_por_tierra") === "true",
    destino: numero("destino"),
  };
}

/** Lo que el motor dice cuando el viaje a una zona del ejemplo no cabe: es de mentira, con su forma. */
export const SIN_VIAJE_A_CUZCO: NonNullable<Respuesta["sin_resultado"]> = {
  motivo:
    "En 2 días no da para ir de Lima a Cuzco y volver: por carretera, solo la ida toma unas 22 horas, y en avión, ir y volver son unas 9 horas: demasiado para 2 días.",
  sugerencias: [
    { campo: "dias", valor: 3, efecto: "sale el viaje, con vuelo" },
    { campo: "destino", valor: null, efecto: "aparecen 3 viajes" },
  ],
};

/**
 * Los viajes del ejemplo, con la consulta que se pidió: el motor siempre la devuelve. Con un
 * destino, solo el de esa zona; si no es una del ejemplo, la explicación de mentira.
 */
export function viajesPara(url: URL): Respuesta {
  const consulta = consultaDe(url);
  if (consulta.destino == null) return { ...RESPUESTA, consulta };
  const rutas = RESPUESTA.rutas.filter((r) => r.polo.id === consulta.destino);
  return { ...RESPUESTA, consulta, rutas, sin_resultado: rutas.length > 0 ? null : SIN_VIAJE_A_CUZCO };
}

/** Las zonas que la app busca: algunas de verdad (public/destinos.json), con pocos lugares. */
export const DESTINOS: Destinos = {
  version_datos: VERSION,
  zonas: [
    {
      id: 36,
      nombre: "Cuzco",
      region: "Cusco",
      regiones: ["Cusco", "Apurímac"],
      peso: 126,
      misma_ciudad: ["cusco"],
      lugares: [
        ["Centro Histórico del Cusco", 4],
        ["Parque Arqueológico Nacional de Saqsaywaman", 4],
        ["Calle Hatunrumiyoc", 3],
      ],
    },
    {
      id: 31,
      nombre: "Miraflores",
      region: "Lima",
      regiones: ["Lima", "Callao"],
      peso: 90,
      misma_ciudad: ["lima"],
      lugares: [
        ["Centro Histórico de Lima", 4],
        ["Centro Comercial Larcomar", 3],
      ],
    },
    {
      id: 139,
      nombre: "Trujillo",
      region: "La Libertad",
      regiones: ["La Libertad"],
      peso: 58,
      misma_ciudad: ["trujillo"],
      lugares: [
        ["Complejo Arqueológico Chan Chan", 4],
        ["Balneario de Huanchaco", 3],
      ],
    },
    {
      id: 27,
      nombre: "Nasca",
      region: "Ica",
      regiones: ["Ica"],
      peso: 50,
      misma_ciudad: [],
      lugares: [
        ["Líneas y Geoglifos de Nasca y Palpa", 4],
        ["Centro Ceremonial Cahuachi", 3],
      ],
    },
    {
      id: 4,
      nombre: "Machupicchu Pueblo",
      region: "Cusco",
      regiones: ["Cusco"],
      peso: 46,
      misma_ciudad: [],
      lugares: [
        ["Parque Arqueológico Nacional de Machu Picchu", 4],
        ["Cascada de Aguas Calientes", 2],
      ],
    },
    {
      id: 71,
      nombre: "Yanque",
      region: "Arequipa",
      regiones: ["Arequipa"],
      peso: 46,
      misma_ciudad: [],
      lugares: [
        ["Valle del Colca", 4],
        ["Aguas Termales de Sallihua", 2],
      ],
    },
    {
      id: 33,
      nombre: "Huancayo",
      region: "Junín",
      regiones: ["Junín"],
      peso: 32,
      misma_ciudad: ["huancayo"],
      lugares: [
        ["Convento de Santa Rosa de Ocopa", 3],
        ["Santuario Arqueológico de Wariwillka", 3],
        ["Basílica Menor Catedral de Huancayo", 2],
      ],
    },
    {
      id: 147,
      nombre: "Sangalle",
      region: "Arequipa",
      regiones: ["Arequipa"],
      peso: 8,
      misma_ciudad: [],
      lugares: [
        ["Cañon del Colca", 2],
        ["Valle de Sangalle", 2],
      ],
    },
  ],
};

const POR_DEFECTO: Record<string, Contestar> = {
  "/v1/opciones": () => ({ cuerpo: OPCIONES }),
  "/v1/viajes": (url) => ({ cuerpo: viajesPara(url) }),
  [`/v1/polos/${POLO.polo.id}`]: () => ({ cuerpo: POLO }),
  "/v1/eventos": () => ({ cuerpo: EVENTOS }),
  "/destinos.json": () => ({ cuerpo: DESTINOS }),
};

/**
 * Reemplaza `fetch` por un API de mentira. `rutas` cambia lo que contesta cada ruta: un
 * cuerpo fijo o una función de la URL. Devuelve el `fetch` falso, para ver qué se pidió.
 */
export function ponerApi(rutas: Record<string, Contestar | Contestacion> = {}) {
  olvidarPedidos(); // lo que respondió el API anterior no vale para este
  olvidarDestinos();
  const tabla: Record<string, Contestar | Contestacion> = { ...POR_DEFECTO, ...rutas };
  const falso = vi.fn(async (entrada: RequestInfo | URL, opciones?: RequestInit): Promise<Response> => {
    const url = new URL(String(entrada));
    const contestar = tabla[url.pathname];
    if (!contestar) return new Response(JSON.stringify({ detail: "No existe." }), { status: 404 });
    const pedido: PedidoRecibido = {
      metodo: opciones?.method ?? "GET",
      cabeceras: new Headers(opciones?.headers),
      cuerpo: typeof opciones?.body === "string" ? JSON.parse(opciones.body) : undefined,
    };
    const { estado = 200, cuerpo } = typeof contestar === "function" ? contestar(url, pedido) : contestar;
    return new Response(JSON.stringify(cuerpo), {
      status: estado,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", falso);
  return falso;
}

/** Lo que se pidió a una ruta del API, como «ruta?parámetros», en orden. Sin `metodo`, solo las lecturas. */
export function pedidosA(falso: ReturnType<typeof ponerApi>, ruta: string, metodo = "GET"): string[] {
  return falso.mock.calls
    .filter(([, opciones]) => (opciones?.method ?? "GET") === metodo)
    .map(([entrada]) => new URL(String(entrada)))
    .filter((url) => url.pathname === ruta)
    .map((url) => `${url.pathname}${url.search}`);
}

/**
 * Un `/v1/eventos` que también publica: guarda lo que le llega en `recibidos` y contesta lo
 * que diga `alPublicar` (por defecto, 201 con el evento de muestra).
 */
export function eventosQuePublican(
  recibidos: PedidoRecibido[],
  alPublicar: Contestacion = { estado: 201, cuerpo: PUBLICADO },
): Contestar {
  return (_url, pedido) => {
    if (pedido.metodo !== "POST") return { cuerpo: EVENTOS };
    recibidos.push(pedido);
    return alPublicar;
  };
}

/** Abre la app en una dirección, como si se hubiera escrito en la barra del navegador. */
export function irA(direccion: string): void {
  window.history.replaceState(null, "", direccion);
}
