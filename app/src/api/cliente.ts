// Cliente del API. La URL base se fija al construir la app (VITE_API_URL); si no se da o
// llega vacía, el API local de `uvicorn dreemgo.api.app:app`.

export const URL_API: string = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

/** Un error de validación del contrato, listo para mostrarse junto a su campo. */
export interface ErrorDeCampo {
  campo: string;
  mensaje: string;
  tipo?: string;
}

export type TipoDeError = "red" | "validacion" | "sin_datos" | "no_encontrado" | "sin_permiso" | "servidor";

export class ErrorApi extends Error {
  readonly tipo: TipoDeError;
  readonly campos: ErrorDeCampo[];

  constructor(tipo: TipoDeError, mensaje: string, campos: ErrorDeCampo[] = []) {
    super(mensaje);
    this.name = "ErrorApi";
    this.tipo = tipo;
    this.campos = campos;
  }
}

const ESPERA_MS = 30_000; // el primer pedido puede tardar: el servidor arranca en frío

function camposDe(detalle: unknown): ErrorDeCampo[] {
  if (!Array.isArray(detalle)) return [];
  return detalle
    .filter((d): d is Record<string, unknown> => typeof d === "object" && d !== null)
    .map((d) => ({
      campo: String(d.campo ?? ""),
      mensaje: String(d.mensaje ?? "No es válido."),
      tipo: typeof d.tipo === "string" ? d.tipo : undefined,
    }));
}

async function errorDe(respuesta: Response): Promise<ErrorApi> {
  let detalle: unknown;
  try {
    detalle = ((await respuesta.json()) as { detail?: unknown }).detail;
  } catch {
    detalle = undefined;
  }
  const texto = typeof detalle === "string" ? detalle : undefined;
  if (respuesta.status === 422) {
    const campos = camposDe(detalle);
    return new ErrorApi("validacion", campos[0]?.mensaje ?? texto ?? "La consulta no es válida.", campos);
  }
  if (respuesta.status === 503) {
    return new ErrorApi("sin_datos", texto ?? "El servidor todavía no tiene sus datos cargados.");
  }
  if (respuesta.status === 404) return new ErrorApi("no_encontrado", texto ?? "No existe.");
  if (respuesta.status === 401 || respuesta.status === 403) {
    return new ErrorApi("sin_permiso", texto ?? "No tienes permiso para hacer esto.");
  }
  return new ErrorApi("servidor", texto ?? `El servidor respondió con un error (${respuesta.status}).`);
}

export interface Pedido {
  parametros?: URLSearchParams;
  metodo?: "GET" | "POST";
  cuerpo?: unknown;
  cabeceras?: Record<string, string>;
  senal?: AbortSignal;
}

/** Pide `ruta` al API y devuelve el JSON, o lanza un ErrorApi con un mensaje para el viajero. */
export async function pedir<T>(ruta: string, pedido: Pedido = {}): Promise<T> {
  const consulta = pedido.parametros?.toString();
  const url = `${URL_API}${ruta}${consulta ? `?${consulta}` : ""}`;
  const control = new AbortController();
  const reloj = setTimeout(() => control.abort(), ESPERA_MS);
  pedido.senal?.addEventListener("abort", () => control.abort(), { once: true });
  let respuesta: Response;
  try {
    respuesta = await fetch(url, {
      method: pedido.metodo ?? "GET",
      headers: {
        Accept: "application/json",
        ...(pedido.cuerpo === undefined ? {} : { "Content-Type": "application/json" }),
        ...pedido.cabeceras,
      },
      body: pedido.cuerpo === undefined ? undefined : JSON.stringify(pedido.cuerpo),
      signal: control.signal,
    });
  } catch (causa) {
    if (pedido.senal?.aborted) throw causa; // lo canceló quien lo pidió: no es un error que mostrar
    throw new ErrorApi(
      "red",
      "No pudimos conectar con el servidor. Revisa tu conexión y vuelve a intentarlo en un momento.",
    );
  } finally {
    clearTimeout(reloj);
  }
  if (!respuesta.ok) throw await errorDe(respuesta);
  return (await respuesta.json()) as T;
}
