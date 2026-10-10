// «Guardados»: los viajes que el viajero guarda, en el almacenamiento local de su navegador.
// No hay cuentas ni nada que salga del dispositivo (docs/decisiones/0001). De cada uno se guarda
// su enlace —la consulta y cuál de sus viajes—, no el plan: al abrirlo, el motor lo vuelve a armar.

import { type Consulta, clave } from "./consulta";

export interface ViajeGuardado {
  consulta: Consulta;
  /**
   * Cuál de los viajes de la consulta: 1, 2 o 3, en el orden en que salieron. null: los tres. Así
   * guardaba la app cuando los tres iban en una misma pantalla, y lo guardado entonces se respeta.
   */
  ruta: number | null;
  /** La versión de datos con que se vio el viaje al guardarlo. */
  version: string | null;
  /** El nombre del viaje («Huancayo»). Sin `ruta` no se muestra: va la frase de la consulta. */
  titulo: string;
  /** Cuándo se guardó, en ISO. */
  guardado: string;
}

const LLAVE = "dreemgo.viajes.v1";
const MAXIMO = 30;

function deposito(): Storage | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null; // navegación privada o almacenamiento bloqueado
  }
}

function esConsulta(c: unknown): c is Consulta {
  if (typeof c !== "object" || c === null) return false;
  const consulta = c as Partial<Consulta>;
  return (
    typeof consulta.origen === "string" &&
    typeof consulta.dias === "number" &&
    Array.isArray(consulta.intereses) &&
    (typeof consulta.mes === "number" || typeof consulta.fecha_inicio === "string")
  );
}

// Lo guardado pudo escribirlo otra versión de la app, o alguien a mano: se lee con cuidado.
function esViaje(v: unknown): v is Omit<ViajeGuardado, "ruta"> & { ruta?: unknown } {
  if (typeof v !== "object" || v === null) return false;
  const viaje = v as Partial<ViajeGuardado>;
  return typeof viaje.titulo === "string" && typeof viaje.guardado === "string" && esConsulta(viaje.consulta);
}

function esRuta(ruta: unknown): ruta is number {
  return typeof ruta === "number" && Number.isInteger(ruta) && ruta >= 1 && ruta <= 3;
}

/** Lo que distingue a un guardado de otro: la consulta y cuál de sus viajes. */
export function claveDeViaje(consulta: Consulta, ruta: number | null): string {
  return `${clave(consulta)}#${ruta ?? ""}`;
}

/** Los viajes guardados, del más reciente al más antiguo. */
export function leerViajes(): ViajeGuardado[] {
  const texto = deposito()?.getItem(LLAVE);
  if (!texto) return [];
  try {
    const lista: unknown = JSON.parse(texto);
    if (!Array.isArray(lista)) return [];
    return lista.filter(esViaje).map((v) => ({ ...v, ruta: esRuta(v.ruta) ? v.ruta : null }));
  } catch {
    return [];
  }
}

function escribir(viajes: ViajeGuardado[]): boolean {
  try {
    deposito()?.setItem(LLAVE, JSON.stringify(viajes.slice(0, MAXIMO)));
    return deposito() !== null;
  } catch {
    return false; // sin espacio o sin permiso
  }
}

export function estaGuardado(consulta: Consulta, ruta: number | null): boolean {
  const buscada = claveDeViaje(consulta, ruta);
  return leerViajes().some((v) => claveDeViaje(v.consulta, v.ruta) === buscada);
}

/** Guarda el viaje al principio de la lista; si ya estaba, lo actualiza. */
export function guardarViaje(viaje: ViajeGuardado): boolean {
  const mia = claveDeViaje(viaje.consulta, viaje.ruta);
  return escribir([viaje, ...leerViajes().filter((v) => claveDeViaje(v.consulta, v.ruta) !== mia)]);
}

export function borrarViaje(consulta: Consulta, ruta: number | null): boolean {
  const mia = claveDeViaje(consulta, ruta);
  return escribir(leerViajes().filter((v) => claveDeViaje(v.consulta, v.ruta) !== mia));
}
