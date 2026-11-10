// Dónde cae un evento dentro del viaje, y el viaje para ir a uno. Las fechas son AAAA-MM-DD,
// que se comparan como texto.

import type { Evento } from "./api/tipos";
import type { Consulta } from "./consulta";
import { aIso, fechaLocal } from "./formato";

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

/** Hasta cuántos días dura un evento al que se va con fecha; a uno más largo se va en su mes. */
export const DIAS_PARA_IR_CON_FECHA = 7;

/**
 * La consulta para ir a un evento («Ir a esta fiesta»): a su zona y, si tiene fecha, saliendo la
 * víspera, o el mismo día en un viaje de un día, y nunca antes de hoy. Si dura más de una semana
 * o su fecha está por confirmar, en su mes (o en este, si ya empezó). Lo demás viene de `base`.
 * null si el evento ya terminó o no queda cerca de ninguna zona.
 */
export function viajeAlEvento(e: Evento, base: Consulta, hoy: Date = new Date()): Consulta | null {
  if (e.polo == null) return null;
  const hoyMismo = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  const inicio = e.fecha_inicio ? fechaLocal(e.fecha_inicio) : null;
  const fin = e.fecha_fin ? fechaLocal(e.fecha_fin) : inicio;
  if (fin && fin < hoyMismo) return null;
  const ir = { ...base, destino: e.polo, sorpresa: false };
  const dias = diasDeEvento(e);
  if (!inicio || dias === null || dias > DIAS_PARA_IR_CON_FECHA || e.precision_fecha === "por_confirmar") {
    const cuando = inicio && inicio > hoyMismo ? inicio : hoyMismo;
    return { ...ir, mes: inicio ? cuando.getMonth() + 1 : base.mes, fecha_inicio: null };
  }
  const vispera = new Date(
    inicio.getFullYear(),
    inicio.getMonth(),
    inicio.getDate() - (base.dias > 1 ? 1 : 0),
  );
  const sale = vispera < hoyMismo ? hoyMismo : vispera;
  return { ...ir, fecha_inicio: aIso(sale), mes: sale.getMonth() + 1 };
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
