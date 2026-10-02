// «Mis viajes»: las consultas que el viajero guarda, en el almacenamiento local de su
// navegador. No hay cuentas ni nada que salga del dispositivo (docs/decisiones/0001).

import { type Consulta, clave } from "./consulta";

export interface ViajeGuardado {
  consulta: Consulta;
  /** La versión de datos con que se vio el viaje al guardarlo. */
  version: string | null;
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
function esViaje(v: unknown): v is ViajeGuardado {
  if (typeof v !== "object" || v === null) return false;
  const viaje = v as Partial<ViajeGuardado>;
  return typeof viaje.titulo === "string" && typeof viaje.guardado === "string" && esConsulta(viaje.consulta);
}

/** Los viajes guardados, del más reciente al más antiguo. */
export function leerViajes(): ViajeGuardado[] {
  const texto = deposito()?.getItem(LLAVE);
  if (!texto) return [];
  try {
    const lista: unknown = JSON.parse(texto);
    return Array.isArray(lista) ? lista.filter(esViaje) : [];
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

export function estaGuardado(consulta: Consulta): boolean {
  const buscada = clave(consulta);
  return leerViajes().some((v) => clave(v.consulta) === buscada);
}

/** Guarda el viaje al principio de la lista; si ya estaba, lo actualiza. */
export function guardarViaje(viaje: ViajeGuardado): boolean {
  const mia = clave(viaje.consulta);
  return escribir([viaje, ...leerViajes().filter((v) => clave(v.consulta) !== mia)]);
}

export function borrarViaje(consulta: Consulta): boolean {
  const mia = clave(consulta);
  return escribir(leerViajes().filter((v) => clave(v.consulta) !== mia));
}
