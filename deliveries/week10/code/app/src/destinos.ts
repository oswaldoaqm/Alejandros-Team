// «Quiero ir a…»: las zonas a las que se puede pedir un viaje y cómo se buscan. La lista la
// escribe el pipeline (pipeline/destinos.py) en public/destinos.json, y se busca aquí, sin
// pedirle nada al API: sirve aunque el API todavía esté despertando.

import { lista } from "./formato";

export interface Zona {
  id: number;
  nombre: string;
  region: string;
  regiones: string[];
  /** Lo que valen sus doce lugares más importantes: ordena la lista. */
  peso: number;
  /** Los orígenes a menos de media hora de su base: desde ahí no se arma un viaje con noches. */
  misma_ciudad: string[];
  /** Sus lugares de un día, de mayor a menor jerarquía: [nombre, jerarquía o null]. */
  lugares: [string, number | null][];
}

export interface Destinos {
  version_datos: string;
  /** De más a menos peso. */
  zonas: Zona[];
}

export interface Encontrada {
  zona: Zona;
  /** Por qué salió: por su nombre, por uno de sus lugares o por su región. null: se propone sin buscar. */
  por: "nombre" | "lugar" | "region" | null;
  /** El lugar por el que salió, si salió por uno. */
  lugar: string | null;
}

/** Cuántas zonas propone la hoja sin nada escrito, y cuántas muestra al buscar. */
export const DESTACADAS = 8;
export const ENCONTRADAS = 15;

/** Sin tildes ni mayúsculas: «Junín» y «junin» son lo mismo. */
export function plano(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

/**
 * Una palabra (plana) en la grafía común a quechua y castellano, como la compara el pipeline al
 * elegir fotos (pipeline/fotos.py): «Qorikancha» y «Coricancha», «Cuzco» y «Cusco», «Huaraz» y
 * «Waras» quedan iguales.
 */
export function canonica(palabra: string): string {
  const sinHMuda = (p: string) => p.replace(/h/g, (h, i: number) => (i > 0 && p[i - 1] === "c" ? h : ""));
  let p = palabra.replaceAll("x", "j");
  p = p.replace(/hu(?=[aeio])/g, (hu, i: number) => (i > 0 && p[i - 1] === "c" ? hu : "w"));
  p = p
    .replace(/gu(?=a)/g, "w")
    .replace(/qu(?=[ei])/g, "k")
    .replaceAll("q", "k")
    .replace(/c(?![eih])/g, "k")
    .replace(/c(?=[ei])/g, "s")
    .replaceAll("z", "s")
    .replaceAll("v", "b");
  p = sinHMuda(p).replaceAll("ll", "l").replaceAll("y", "i");
  return p.replace(/(.)\1+/g, "$1");
}

/** Las palabras canónicas de un texto. */
function palabras(texto: string): string[] {
  return plano(texto)
    .split(/[^a-z0-9]+/)
    .filter(Boolean)
    .map(canonica);
}

/**
 * Por dónde puede empezar lo que se busca: desde cada palabra hasta el final, todo junto. Así
 * «machu picchu» encuentra «Machupicchu», y «ica» encuentra «Ica» pero no «Basílica».
 */
function colas(texto: string): string[] {
  const p = palabras(texto);
  return p.map((_, i) => p.slice(i).join(""));
}

interface Fichada {
  zona: Zona;
  nombre: string[];
  regiones: string[][];
  lugares: { nombre: string; jerarquia: number; colas: string[] }[];
}

const fichadas = new WeakMap<Destinos, Fichada[]>();

function fichar(destinos: Destinos): Fichada[] {
  let lista = fichadas.get(destinos);
  if (!lista) {
    lista = destinos.zonas.map((zona) => ({
      zona,
      nombre: colas(zona.nombre),
      regiones: zona.regiones.map(colas),
      lugares: zona.lugares.map(([nombre, jerarquia]) => ({
        nombre,
        jerarquia: jerarquia ?? 0,
        colas: colas(nombre),
      })),
    }));
    fichadas.set(destinos, lista);
  }
  return lista;
}

/**
 * Las zonas que coinciden con lo escrito, las mejores primero: por su nombre (desde el comienzo,
 * y si no, desde otra palabra), por uno de sus lugares (con tres letras o más; primero por el de
 * más jerarquía) y por su región. Entre las que coinciden igual, la de más peso.
 */
export function buscarZonas(destinos: Destinos, texto: string, cuantas = ENCONTRADAS): Encontrada[] {
  const buscado = palabras(texto).join("");
  if (buscado === "") return [];
  const halladas: { encontrada: Encontrada; orden: number }[] = [];
  for (const f of fichar(destinos)) {
    const desde = f.nombre.findIndex((c) => c.startsWith(buscado));
    if (desde >= 0) {
      halladas.push({ encontrada: { zona: f.zona, por: "nombre", lugar: null }, orden: desde === 0 ? 0 : 1 });
      continue;
    }
    const lugar =
      buscado.length >= 3 ? f.lugares.find((l) => l.colas.some((c) => c.startsWith(buscado))) : undefined;
    if (lugar) {
      halladas.push({
        encontrada: { zona: f.zona, por: "lugar", lugar: lugar.nombre },
        orden: 10 - lugar.jerarquia,
      });
      continue;
    }
    if (f.regiones.some((r) => r.some((c) => c.startsWith(buscado)))) {
      halladas.push({ encontrada: { zona: f.zona, por: "region", lugar: null }, orden: 11 });
    }
  }
  // La lista ya va de más a menos peso, y el orden de JavaScript es estable.
  return halladas
    .sort((a, b) => a.orden - b.orden)
    .slice(0, cuantas)
    .map((h) => h.encontrada);
}

/** Las de algún lugar de jerarquía 4, de más a menos peso, sin las de la ciudad de `origen`. */
export function zonasDestacadas(destinos: Destinos, origen: string, cuantas = DESTACADAS): Encontrada[] {
  return destinos.zonas
    .filter((z) => !z.misma_ciudad.includes(origen) && z.lugares.some(([, jerarquia]) => jerarquia === 4))
    .slice(0, cuantas)
    .map((zona) => ({ zona, por: null, lugar: null }));
}

/** Su lugar más importante, para presentarla: «Parque Arqueológico Nacional de Machu Picchu». */
export function lugarPrincipal(zona: Zona): string | null {
  const [primero] = zona.lugares;
  return primero && (primero[1] ?? 0) >= 3 ? primero[0] : null;
}

/**
 * Lo que se lee bajo el nombre de una zona: el lugar por el que salió, sus regiones si salió por
 * ellas o, si no, su lugar más importante.
 */
export function notaDeZona({ zona, por, lugar }: Encontrada): string {
  if (por === "lugar" && lugar) return `Por ${lugar}`;
  if (por === "region") return lista(zona.regiones);
  return lugarPrincipal(zona) ?? lista(zona.regiones);
}

/** El nombre de una zona, o null si la lista no llegó o no la tiene. */
export function nombreDeZona(destinos: Destinos | null | undefined, id: number | null): string | null {
  if (!destinos || id === null) return null;
  return destinos.zonas.find((z) => z.id === id)?.nombre ?? null;
}
