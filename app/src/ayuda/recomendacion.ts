// Interpreta solo datos que el formulario y el API ya admiten. La respuesta
// siempre la calcula el motor de DreemGO; aquí no se inventan destinos.

import type { Opciones } from "../api/tipos";
import { type Consulta, consultaNueva } from "../consulta";
import { MESES } from "../formato";
import type { Vista } from "../ruta";

function simple(texto: string): string {
  return texto
    .toLocaleLowerCase("es-PE")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function pideRecomendacion(texto: string): boolean {
  const frase = simple(texto);
  return (
    /\b(recomiend\w*|sugier\w*|suger\w*|propon\w*|propuest\w*)\b/.test(frase) ||
    /\b(quiero|busco|necesito)\b.*\b(playa|naturaleza|historia|gastronomia|aventura|caminatas?|fiestas?|arquitectura|vida\s+nocturna)\b/.test(
      frase,
    )
  );
}

export function consultaDeVista(vista: Vista): Consulta {
  if ("consulta" in vista && vista.consulta) return vista.consulta;
  return consultaNueva();
}

export type Preparacion = { consulta: Consulta; aviso: string | null } | { error: string };

export function prepararConsulta(texto: string, base: Consulta, opciones: Opciones): Preparacion {
  const frase = simple(texto);
  const consulta: Consulta = { ...base, intereses: [...base.intereses], sorpresa: false };
  const meses = [...MESES.map(simple)];
  meses[8] = "setiembre";
  const mesEncontrado = meses.findIndex((nombre) => new RegExp(`\\b${nombre}\\b`).test(frase));
  if (mesEncontrado >= 0) {
    consulta.mes = mesEncontrado + 1;
    consulta.fecha_inicio = null;
  } else if (/\bseptiembre\b/.test(frase)) {
    consulta.mes = 9;
    consulta.fecha_inicio = null;
  }

  const dias = frase.match(/\b(\d{1,2})\s*dias?\b/);
  if (dias) {
    const cantidad = Number(dias[1]);
    if (cantidad < opciones.dias.minimo || cantidad > opciones.dias.maximo) {
      return { error: `El viaje puede durar entre ${opciones.dias.minimo} y ${opciones.dias.maximo} días.` };
    }
    consulta.dias = cantidad;
  }

  const monto = frase.match(
    /(?:\bs\/\s*|\bpresupuesto\s+(?:de\s+|hasta\s+)?|\bhasta\s+s\/\s*)(\d[\d\s.,]*)\s*(?:soles)?/,
  );
  if (monto) {
    const presupuesto = Number((monto[1] ?? "").replace(/[\s.,]/g, ""));
    if (presupuesto < opciones.presupuesto.minimo || presupuesto > opciones.presupuesto.maximo) {
      return {
        error: `El presupuesto por persona debe estar entre S/ ${opciones.presupuesto.minimo} y S/ ${opciones.presupuesto.maximo}.`,
      };
    }
    consulta.presupuesto = presupuesto;
  }

  const origenes = [...opciones.origenes].sort((a, b) => b.nombre.length - a.nombre.length);
  const origen = origenes.find((opcion) =>
    new RegExp(`\\bdesde\\s+${simple(opcion.nombre).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`).test(frase),
  );
  if (origen) consulta.origen = origen.id;
  else if (/\bdesde\s+[a-z]/.test(frase)) {
    return { error: "No reconozco esa ciudad de salida. Elígela en el planificador." };
  }

  const intereses = opciones.intereses.filter(({ id, etiqueta }) => {
    const nombres = [id.replaceAll("_", " "), simple(etiqueta)];
    return nombres.some((nombre) => new RegExp(`\\b${nombre}\\b`).test(frase));
  });
  if (intereses.length > 0) consulta.intereses = intereses.map(({ id }) => id);

  if (consulta.mes === null && consulta.fecha_inicio === null) consulta.mes = consultaNueva().mes;
  const aviso = /\b(?:viaje|ruta|ir)\s+a\s+(?!la\s+playa\b|la\s+naturaleza\b)[a-z]/.test(frase)
    ? "Si buscas una ciudad específica, elige «A dónde» en el planificador para fijarla."
    : null;
  return { consulta, aviso };
}
