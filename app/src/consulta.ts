// La consulta del viajero y su ida y vuelta a la URL. El enlace es el viaje guardado
// (docs/decisiones/0001): los mismos parámetros que recibe GET /v1/viajes, más `v`, la
// versión de datos con que se calculó.

import { fechaLocal, lista, mayuscula, mes, metros, plural, soles } from "./formato";

export interface Consulta {
  origen: string;
  mes: number | null;
  fecha_inicio: string | null;
  dias: number;
  intereses: string[];
  presupuesto: number | null;
  altitud_max: number | null;
  sorpresa: boolean;
}

export const POR_DEFECTO: Consulta = {
  origen: "lima",
  mes: null,
  fecha_inicio: null,
  dias: 6,
  intereses: [],
  presupuesto: null,
  altitud_max: null,
  sorpresa: false,
};

function entero(texto: string | null): number | null {
  if (texto === null || !/^-?\d+$/.test(texto.trim())) return null;
  return Number(texto);
}

/** Los parámetros que entiende el API, en orden fijo. Sin `v` ni nada de la app. */
export function aParametros(c: Consulta): URLSearchParams {
  const p = new URLSearchParams();
  p.set("origen", c.origen);
  if (c.fecha_inicio) p.set("fecha_inicio", c.fecha_inicio);
  else if (c.mes !== null) p.set("mes", String(c.mes));
  p.set("dias", String(c.dias));
  for (const interes of c.intereses) p.append("intereses", interes);
  if (c.presupuesto !== null) p.set("presupuesto", String(c.presupuesto));
  if (c.altitud_max !== null) p.set("altitud_max", String(c.altitud_max));
  if (c.sorpresa) p.set("sorpresa", "true");
  return p;
}

/** La consulta de una URL, o null si no trae mes ni fecha: sin eso no hay viaje que pedir. */
export function deParametros(p: URLSearchParams): Consulta | null {
  const fecha = p.get("fecha_inicio");
  const mesPedido = entero(p.get("mes"));
  if (!fecha && mesPedido === null) return null;
  const intereses = [...new Set(p.getAll("intereses").filter(Boolean))];
  const deLaFecha = fecha ? fechaLocal(fecha) : null;
  return {
    origen: p.get("origen")?.trim() || POR_DEFECTO.origen,
    mes: deLaFecha ? deLaFecha.getMonth() + 1 : mesPedido,
    fecha_inicio: fecha || null,
    dias: entero(p.get("dias")) ?? POR_DEFECTO.dias,
    intereses,
    presupuesto: entero(p.get("presupuesto")),
    altitud_max: entero(p.get("altitud_max")),
    sorpresa: p.get("sorpresa") === "true" || p.get("sorpresa") === "1",
  };
}

/** La consulta como texto, para comparar dos y para la clave de «Mis viajes». */
export function clave(c: Consulta): string {
  const p = aParametros({ ...c, intereses: [...c.intereses].sort() });
  return p.toString();
}

/** Los parámetros del enlace para compartir: la consulta más la versión de datos. */
export function aEnlace(c: Consulta, version?: string | null): string {
  const p = aParametros(c);
  if (version) p.set("v", version);
  return `?${p.toString()}`;
}

export interface Nombres {
  origenes: Record<string, string>;
  intereses: Record<string, string>;
}

/** El nombre de la ciudad de origen; si las opciones todavía no llegaron, su identificador legible. */
export function nombreDeOrigen(id: string, nombres: Nombres): string {
  return nombres.origenes[id] ?? mayuscula(id.replaceAll("-", " "));
}

/**
 * La consulta en una frase, como la diría una persona: «Desde Lima, 6 días en julio», o «desde
 * el 20 de julio» si ya tiene fecha. Es el título de la pestaña y el nombre de un viaje guardado.
 */
export function titulo(c: Consulta, nombres: Nombres): string {
  const f = c.fecha_inicio ? fechaLocal(c.fecha_inicio) : null;
  const cuando = f ? `desde el ${f.getDate()} de ${mes(f.getMonth() + 1)}` : `en ${mes(c.mes)}`;
  return `Desde ${nombreDeOrigen(c.origen, nombres)}, ${plural(c.dias, "día", "días")} ${cuando}`;
}

/** Lo demás que pidió, si pidió algo: «Playa, hasta S/ 1 800 por persona, solo fuera de Lima y Cusco». */
export function detalles(c: Consulta, nombres: Nombres): string | null {
  const partes: string[] = [];
  if (c.intereses.length > 0) partes.push(lista(c.intereses.map((i) => nombres.intereses[i] ?? i)));
  if (c.presupuesto !== null) partes.push(`hasta ${soles(c.presupuesto)} por persona`);
  if (c.altitud_max !== null) partes.push(`hasta ${metros(c.altitud_max)} de altura`);
  if (c.sorpresa) partes.push("solo fuera de Lima y Cusco");
  return partes.length > 0 ? mayuscula(partes.join(", ")) : null;
}
