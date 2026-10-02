// La consulta del viajero y su ida y vuelta a la URL. El enlace es el viaje guardado
// (docs/decisiones/0001): los mismos parámetros que recibe GET /v1/viajes, más `v`, la
// versión de datos con que se calculó.

import { fechaLocal, mayuscula, mes, metros, plural, soles } from "./formato";

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

/** Una pieza de la consulta, para pintarla como chip y poder quitarla. */
export interface Pieza {
  campo: keyof Consulta;
  valor?: string;
  texto: string;
  /** La consulta sin esta pieza, o null si no se puede quitar (el mes es obligatorio). */
  sin: Consulta | null;
}

/** La consulta en piezas legibles: «Desde Lima», «6 días», «Julio», «Hasta S/ 1 800»… */
export function piezas(c: Consulta, nombres: Nombres): Pieza[] {
  const lista: Pieza[] = [
    {
      campo: "origen",
      texto: `Desde ${nombreDeOrigen(c.origen, nombres)}`,
      sin: c.origen === POR_DEFECTO.origen ? null : { ...c, origen: POR_DEFECTO.origen },
    },
    {
      campo: "dias",
      texto: plural(c.dias, "día", "días"),
      sin: c.dias === POR_DEFECTO.dias ? null : { ...c, dias: POR_DEFECTO.dias },
    },
  ];
  if (c.fecha_inicio) {
    const f = fechaLocal(c.fecha_inicio);
    lista.push({
      campo: "fecha_inicio",
      texto: f ? `Sale el ${f.getDate()} de ${mes(f.getMonth() + 1)}` : c.fecha_inicio,
      sin: { ...c, fecha_inicio: null, mes: f ? f.getMonth() + 1 : c.mes },
    });
  } else if (c.mes !== null) {
    lista.push({ campo: "mes", texto: mayuscula(mes(c.mes)) || `Mes ${c.mes}`, sin: null });
  }
  for (const interes of c.intereses) {
    lista.push({
      campo: "intereses",
      valor: interes,
      texto: nombres.intereses[interes] ?? interes,
      sin: { ...c, intereses: c.intereses.filter((i) => i !== interes) },
    });
  }
  if (c.presupuesto !== null) {
    lista.push({
      campo: "presupuesto",
      texto: `Hasta ${soles(c.presupuesto)}`,
      sin: { ...c, presupuesto: null },
    });
  }
  if (c.altitud_max !== null) {
    lista.push({
      campo: "altitud_max",
      texto: `Hasta ${metros(c.altitud_max)}`,
      sin: { ...c, altitud_max: null },
    });
  }
  if (c.sorpresa) lista.push({ campo: "sorpresa", texto: "Sorpréndeme", sin: { ...c, sorpresa: false } });
  return lista;
}

/** Un título corto para la pestaña y para «Mis viajes»: «Lima · julio · 6 días». */
export function titulo(c: Consulta, nombres: Nombres): string {
  const cuando = c.fecha_inicio
    ? (() => {
        const f = fechaLocal(c.fecha_inicio);
        return f ? `${f.getDate()} de ${mes(f.getMonth() + 1)}` : c.fecha_inicio;
      })()
    : mes(c.mes);
  const partes = [nombreDeOrigen(c.origen, nombres), cuando, plural(c.dias, "día", "días")];
  const gustos = c.intereses.map((i) => (nombres.intereses[i] ?? i).toLowerCase());
  if (gustos.length) partes.push(gustos.slice(0, 2).join(" y ") + (gustos.length > 2 ? "…" : ""));
  if (c.sorpresa) partes.push("sorpréndeme");
  return partes.filter(Boolean).join(" · ");
}
