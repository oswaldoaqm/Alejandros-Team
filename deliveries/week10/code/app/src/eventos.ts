// Dónde cae un evento dentro del viaje. Las fechas son AAAA-MM-DD, que se comparan como texto.

import type { Evento } from "./api/tipos";
import { fechaLocal } from "./formato";

const DIA_MS = 24 * 60 * 60 * 1000;
/** Hasta cuántos días dura un evento que se anota en su día; los más largos van aparte. */
export const DIAS_DE_UN_EVENTO_PUNTUAL = 3;

/** Cuántos días dura; null si no tiene fecha. */
export function diasDeEvento(e: Pick<Evento, "fecha_inicio" | "fecha_fin">): number | null {
  const inicio = e.fecha_inicio ? fechaLocal(e.fecha_inicio) : null;
  if (!inicio) return null;
  const fin = e.fecha_fin ? fechaLocal(e.fecha_fin) : null;
  if (!fin || fin < inicio) return 1;
  return Math.round((fin.getTime() - inicio.getTime()) / DIA_MS) + 1;
}

/** Si el evento ocurre el día `iso`. */
export function caeEn(e: Pick<Evento, "fecha_inicio" | "fecha_fin">, iso: string): boolean {
  if (!e.fecha_inicio) return false;
  return e.fecha_inicio <= iso && iso <= (e.fecha_fin ?? e.fecha_inicio);
}

/**
 * Los eventos que se anotan en un día del itinerario: los que caen ese día y duran poco.
 * Uno que dura todo el mes diría lo mismo en cada día; ese se queda en la lista general.
 */
export function eventosDelDia<E extends Pick<Evento, "fecha_inicio" | "fecha_fin">>(
  eventos: readonly E[],
  iso: string | null | undefined,
): E[] {
  if (!iso) return [];
  return eventos.filter((e) => {
    const dias = diasDeEvento(e);
    return dias !== null && dias <= DIAS_DE_UN_EVENTO_PUNTUAL && caeEn(e, iso);
  });
}
