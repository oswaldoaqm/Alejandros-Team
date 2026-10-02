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
