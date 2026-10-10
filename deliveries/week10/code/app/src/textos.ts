// Frases cortas que la app arma con los datos del contrato. Lo que ya viene escrito del
// motor (motivos, avisos, notas, explicaciones) se muestra tal cual: aquí no se reescribe.

import type { Dia, Medio, Recurso, Sugerencia } from "./api/tipos";
import type { Consulta, Nombres } from "./consulta";
import { fecha, lista, mes, metros, plural, soles, solesExactos } from "./formato";

const TIPO_DE_DIA: Record<Dia["tipo"], string> = {
  ida: "Ida",
  visita: "Visitas",
  vuelta: "Vuelta",
  ida_y_visita: "Ida y visitas",
  visita_y_vuelta: "Visitas y vuelta",
  ida_visita_y_vuelta: "Ida, visitas y vuelta",
};

/** Qué se hace ese día: «Ida y visitas», «Día libre»… */
export function tipoDeDia(dia: Pick<Dia, "tipo" | "paradas">): string {
  if (dia.tipo === "visita" && (dia.paradas ?? []).length === 0) return "Día libre";
  return TIPO_DE_DIA[dia.tipo];
}

const CON_QUE: Record<Medio, string> = { carretera: "por carretera", tren: "en tren", bote: "en bote" };

/** «por carretera», «por carretera y en bote»: con las palabras del motor. */
export function conQueSeViaja(medios: readonly Medio[] | null | undefined): string {
  const dichos = (medios ?? []).map((m) => CON_QUE[m]);
  return dichos.length > 0 ? lista(dichos) : CON_QUE.carretera;
}

/** Lo que la ficha dice del ingreso. Si no publica la tarifa, se dice: no se inventa. */
export function entrada(recurso: Pick<Recurso, "ingreso" | "tarifa_soles">): string {
  if (recurso.ingreso === "libre") return "Entrada libre";
  if (recurso.ingreso === "pagado") {
    return recurso.tarifa_soles != null && recurso.tarifa_soles > 0
      ? `Entrada ${solesExactos(recurso.tarifa_soles)}`
      : "Entrada pagada, sin tarifa publicada";
  }
  return "La ficha no dice si se paga";
}

/** La consulta que resulta de aceptar una sugerencia del motor, o null si no se entiende. */
export function aplicarSugerencia(c: Consulta, s: Sugerencia): Consulta | null {
  const { campo, valor } = s;
  switch (campo) {
    case "dias":
      return typeof valor === "number" ? { ...c, dias: valor } : null;
    case "altitud_max":
    case "presupuesto":
      return valor === null || typeof valor === "number" ? { ...c, [campo]: valor } : null;
    case "intereses":
      if (valor === null) return { ...c, intereses: [] };
      return Array.isArray(valor) ? { ...c, intereses: valor } : null;
    case "mes":
      return typeof valor === "number" ? { ...c, mes: valor, fecha_inicio: null } : null;
    case "fecha_inicio":
      if (valor === null) return { ...c, fecha_inicio: null };
      return typeof valor === "string" ? { ...c, fecha_inicio: valor } : null;
    case "origen":
      return typeof valor === "string" ? { ...c, origen: valor } : null;
  }
}

/** La sugerencia como una acción: «Probar con 8 días», «Quitar el límite de altitud». */
export function textoDeSugerencia(s: Sugerencia, nombres: Nombres): string {
  const { campo, valor } = s;
  switch (campo) {
    case "dias":
      return typeof valor === "number" ? `Probar con ${plural(valor, "día", "días")}` : "Cambiar los días";
    case "altitud_max":
      return typeof valor === "number"
        ? `Subir el límite de altitud a ${metros(valor)}`
        : "Quitar el límite de altitud";
    case "presupuesto":
      return typeof valor === "number" ? `Probar con ${soles(valor)}` : "Quitar el tope de presupuesto";
    case "intereses":
      return Array.isArray(valor) && valor.length > 0
        ? `Buscar solo ${lista(valor.map((i) => (nombres.intereses[i] ?? i).toLowerCase()))}`
        : "Buscar sin filtrar por intereses";
    case "mes":
      return typeof valor === "number" ? `Probar en ${mes(valor)}` : "Cambiar el mes";
    case "fecha_inicio":
      return typeof valor === "string" ? `Salir el ${fecha(valor)}` : "Buscar por mes, sin fecha fija";
    case "origen":
      return typeof valor === "string"
        ? `Salir desde ${nombres.origenes[valor] ?? valor}`
        : "Cambiar el origen";
  }
}

// ── El rediseño: cómo se nombra y se resume un viaje para quien lo elige ──────────────

/**
 * El nombre del viaje en dos partes. El motor desambigua las zonas que comparten base con
 * «Base · lugar principal»: arriba va la base y abajo, si hay, su lugar principal.
 */
export function nombreDelViaje(nombre: string): { titulo: string; subtitulo: string | null } {
  const [titulo = nombre, ...resto] = nombre.split(" · ");
  return { titulo, subtitulo: resto.length > 0 ? resto.join(" · ") : null };
}

/** Los imperdibles: los lugares de jerarquía 3 o 4, de mayor a menor, sin repetir. */
export function imperdibles(dias: readonly Dia[]): string[] {
  const vistos = new Map<string, number>();
  for (const dia of dias)
    for (const p of dia.paradas ?? [])
      if ((p.recurso.jerarquia ?? 0) >= 3) vistos.set(p.recurso.nombre, p.recurso.jerarquia ?? 0);
  return [...vistos.entries()].sort((a, b) => b[1] - a[1]).map(([nombre]) => nombre);
}

/** Cuántos lugares visita el viaje en total. */
export function lugaresDelViaje(dias: readonly Dia[]): number {
  return dias.reduce((suma, d) => suma + (d.paradas ?? []).length, 0);
}

/** Lo que dice el veredicto del mes, en palabras de viajero. */
export function climaCorto(
  veredicto: "viable" | "advertencia" | "desaconsejado",
  mesDelViaje: number,
): string {
  if (veredicto === "viable") return `Buen clima en ${mes(mesDelViaje)}`;
  if (veredicto === "advertencia") return `Puede llover en ${mes(mesDelViaje)}`;
  return `Temporada de lluvias en ${mes(mesDelViaje)}`;
}

/** Una altura que vale la pena avisar: desde 2 500 m el cuerpo la siente. */
export const ALTURA_QUE_SE_SIENTE = 2500;

/**
 * De los motivos del motor, los que dicen algo que la pantalla del viaje no dice ya en otro
 * lado: los imperdibles van con su estrella, y el clima y el tiempo de ida van en los datos de
 * arriba. Se reconocen por las frases fijas del motor (dreemgo/motor/viaje.py, `motivos`); si
 * una cambia, lo peor que pasa es que algo se lea dos veces.
 */
export function razonesQueFaltan(motivos: readonly string[]): string[] {
  return motivos.filter((m) => !/jerarqu[ií]a/i.test(m) && !/temporada seca/i.test(m) && !/^A \d/.test(m));
}

/** El clima del mes en dos o tres palabras, para los datos de arriba del viaje. */
export const CLIMA_EN_POCAS_PALABRAS: Record<"viable" | "advertencia" | "desaconsejado", string> = {
  viable: "Buen clima",
  advertencia: "Puede llover",
  desaconsejado: "Lluvias",
};

/** «Catedral de Huancayo, Plaza Huamanmarca y 4 lugares más». */
export function resumenDeLugares(nombres: readonly string[], cuantos = 2): string {
  if (nombres.length <= cuantos + 1) return lista([...nombres]);
  const resto = nombres.length - cuantos;
  return `${nombres.slice(0, cuantos).join(", ")} y ${resto} lugares más`;
}
