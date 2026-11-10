// Las fotos de los lugares y de los pueblos donde se duerme. Son de Wikimedia Commons, las elige
// el pipeline (pipeline/fotos.py) y su lista va en public/fotos.json. La app no guarda fotos:
// las pide a Wikimedia, del tamaño que necesita cada pantalla, y muestra su autor y su licencia.

import type { Polo, Recurso, Ruta } from "./api/tipos";

export interface Foto {
  /** El nombre del archivo en Commons, con espacios. */
  archivo: string;
  /** Su carpeta en upload.wikimedia.org: «b/bb». */
  ruta: string;
  ancho: number;
  alto: number;
  autor: string;
  licencia: string;
  url_licencia: string;
  wikidata: string;
}

export interface Fotos {
  version_datos: string;
  /** Por código de recurso. */
  lugares: Record<string, Foto>;
  /** Por id de polo: la foto del pueblo donde se duerme. */
  bases: Record<string, Foto>;
}

/** Una foto y lo que muestra. */
export interface FotoDe {
  foto: Foto;
  de: string;
}

const COMMONS = "https://upload.wikimedia.org/wikipedia/commons";

/** Los anchos que Wikimedia sirve como miniatura: cualquier otro responde con un error. */
const ANCHOS = [330, 500, 960, 1280];

function enUrl(archivo: string): string {
  return encodeURIComponent(archivo.replaceAll(" ", "_"));
}

/** La foto de `ancho` píxeles, o la original si es más chica que eso. */
export function urlDeFoto(foto: Foto, ancho: number): string {
  const nombre = enUrl(foto.archivo);
  if (ancho >= foto.ancho) return `${COMMONS}/${foto.ruta}/${nombre}`;
  return `${COMMONS}/thumb/${foto.ruta}/${nombre}/${ancho}px-${nombre}`;
}

/** Las miniaturas hasta `tope` píxeles, para `srcset`: el navegador elige la que le sirve. */
export function srcsetDeFoto(foto: Foto, tope = 1280): string {
  const caben = ANCHOS.filter((a) => a <= tope);
  const anchos = caben.filter((a) => a < foto.ancho);
  const lista = anchos.map((a) => `${urlDeFoto(foto, a)} ${a}w`);
  // Si la original es más chica que alguna de las que caben, va ella con su ancho real.
  if (anchos.length < caben.length) lista.push(`${urlDeFoto(foto, foto.ancho)} ${foto.ancho}w`);
  return lista.join(", ");
}

/** La página de la foto en Commons: ahí están su autor, su licencia y la original. */
export function paginaDeFoto(foto: Foto): string {
  return `https://commons.wikimedia.org/wiki/File:${enUrl(foto.archivo)}`;
}

/**
 * «CC BY-SA 4.0», tal como la nombra Commons. En castellano van las dos que no son una sigla:
 * «dominio público» y «con atribución», la que solo pide nombrar al autor.
 */
export function licenciaDeFoto(foto: Foto): string {
  if (/^(public domain|pd)/i.test(foto.licencia)) return "dominio público";
  if (/^attribution$/i.test(foto.licencia)) return "con atribución";
  return foto.licencia;
}

/** «Foto: Autora, CC BY-SA 4.0». */
export function creditoDeFoto(foto: Foto): string {
  return foto.autor ? `Foto: ${foto.autor}, ${licenciaDeFoto(foto)}` : `Foto de ${licenciaDeFoto(foto)}`;
}

const apaisada = (foto: Foto) => foto.ancho >= foto.alto;

type Lugar = Pick<Recurso, "codigo" | "nombre" | "jerarquia">;

/**
 * La foto que representa a un grupo de lugares: la de un imperdible (de mayor a menor
 * jerarquía; entre iguales, el primero de la lista), después la del pueblo donde se duerme y al
 * final la de cualquier otro lugar. En cada paso, primero las apaisadas: en una tarjeta o una
 * portada, una foto vertical se recorta demasiado.
 */
function fotoDeLugares(lugares: readonly Lugar[], base: FotoDe | null, fotos: Fotos): FotoDe | null {
  const porJerarquia = [...lugares].sort((a, b) => (b.jerarquia ?? 0) - (a.jerarquia ?? 0));
  const conFoto = (grupo: Lugar[]): FotoDe[] =>
    grupo.flatMap((l) => {
      const foto = fotos.lugares[l.codigo];
      return foto ? [{ foto, de: l.nombre }] : [];
    });
  const pasos: FotoDe[][] = [
    conFoto(porJerarquia.filter((l) => (l.jerarquia ?? 0) >= 3)),
    base ? [base] : [],
    conFoto(porJerarquia.filter((l) => (l.jerarquia ?? 0) < 3)),
  ];
  for (const paso of pasos) {
    const elegida = paso.find((f) => apaisada(f.foto)) ?? paso[0];
    if (elegida) return elegida;
  }
  return null;
}

function fotoDeLaBase(polo: Pick<Polo, "id" | "base">, fotos: Fotos): FotoDe | null {
  const foto = fotos.bases[String(polo.id)];
  return foto ? { foto, de: polo.base.nombre } : null;
}

/** La foto de un viaje: la de su imperdible principal, en el orden del viaje. */
export function fotoDelViaje(ruta: Ruta, fotos: Fotos): FotoDe | null {
  const lugares = ruta.dias.flatMap((d) => (d.paradas ?? []).map((p) => p.recurso));
  return fotoDeLugares(lugares, fotoDeLaBase(ruta.polo, fotos), fotos);
}

/** La foto de una zona, con el mismo criterio que la de un viaje. */
export function fotoDeLaZona(
  polo: Pick<Polo, "id" | "base">,
  recursos: readonly Lugar[],
  fotos: Fotos,
): FotoDe | null {
  return fotoDeLugares(recursos, fotoDeLaBase(polo, fotos), fotos);
}
