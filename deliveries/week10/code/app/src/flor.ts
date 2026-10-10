// La flor del viaje. En la tarjeta y en la portada, un viaje es una flor: el tallo es el camino de
// ida (más largo cuanto más lejos queda la zona) y cada pétalo es un día allá: más largo cuanto
// más lejos llegas ese día desde donde duermes, más ancho cuantos más lugares visitas. Así dos
// viajes se comparan de un vistazo. En el mapa, el pétalo de cada día es su forma real: la
// porción de la zona que recorre, desde la base (docs/decisiones/0009: el viaje es una estrella).

export interface PuntoDelViaje {
  lat: number;
  lon: number;
  dia: number;
}

export interface Plano {
  x: number;
  y: number;
}

export interface Petalo {
  dia: number;
  /** El trazo del pétalo, en coordenadas del dibujo. */
  d: string;
}

export interface Flor {
  /** Donde se duerme: de ahí salen los pétalos. */
  centro: Plano;
  /** El camino de ida, de la flor hacia abajo; null si no se sabe cuánto toma. */
  tallo: string | null;
  petalos: Petalo[];
}

/** Lo que la flor necesita de cada día: cuántos lugares y hasta dónde se llega. */
export interface DiaDeLaFlor {
  dia: number;
  lugares: number;
  /** La distancia en línea recta, en km, del lugar más lejano a donde se duerme. */
  alcanceKm: number;
}

type Par = [number, number];

const fmt = (v: number) => (Math.round(v * 100) / 100).toString();

/** Distancia en línea recta entre dos puntos, en km. */
export function kmEntre(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLon = (b.lon - a.lon) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(h)));
}

// ── La flor del viaje, resumida ────────────────────────────────────────────────────

/**
 * Los días con lugares, como los resume la flor. Sin base (un viaje de ida y vuelta en el día),
 * el alcance se mide desde el centro de los lugares.
 */
export function diasDeLaFlor(
  base: { lat: number; lon: number } | null,
  puntos: readonly PuntoDelViaje[],
): DiaDeLaFlor[] {
  if (puntos.length === 0) return [];
  const desde = base ?? {
    lat: puntos.reduce((s, p) => s + p.lat, 0) / puntos.length,
    lon: puntos.reduce((s, p) => s + p.lon, 0) / puntos.length,
  };
  const dias = [...new Set(puntos.map((p) => p.dia))].sort((a, b) => a - b);
  return dias.map((dia) => {
    const delDia = puntos.filter((p) => p.dia === dia);
    return { dia, lugares: delDia.length, alcanceKm: Math.max(0, ...delDia.map((p) => kmEntre(desde, p))) };
  });
}

/** Un pétalo de `largo` en el ángulo `grados`, con la panza a `ancho` veces su largo. */
function petalo(centro: Plano, grados: number, largo: number, ancho: number): string {
  const a = (grados * Math.PI) / 180;
  const dir = { x: Math.cos(a), y: Math.sin(a) };
  const per = { x: -dir.y, y: dir.x };
  const w = ancho * largo;
  const en = (t: number, lado: number) =>
    `${fmt(centro.x + dir.x * largo * t + per.x * lado)} ${fmt(centro.y + dir.y * largo * t + per.y * lado)}`;
  const c = `${fmt(centro.x)} ${fmt(centro.y)}`;
  return `M${c} C${en(0.3, w)} ${en(0.92, 0.55 * w)} ${en(1, 0)} C${en(0.92, -0.55 * w)} ${en(0.3, -w)} ${c} Z`;
}

/**
 * La flor de un viaje en un cuadrado de 100: un pétalo por día con lugares y, si se sabe cuánto
 * toma la ida, un tallo. Las medidas son absolutas (no relativas al viaje): un pétalo largo es
 * un día que va lejos en cualquier viaje, y dos flores se comparan entre sí.
 */
export function florDelViaje(dias: readonly DiaDeLaFlor[], horasDeIda: number | null = null): Flor {
  const conTallo = horasDeIda !== null && horasDeIda > 0;
  const centro = { x: 50, y: conTallo ? 44 : 50 };
  let tallo: string | null = null;
  if (conTallo) {
    const largo = 10 + 5 * Math.min(horasDeIda, 7);
    const { x, y } = centro;
    tallo = `M${fmt(x)} ${fmt(y)} C${fmt(x + 5)} ${fmt(y + largo * 0.35)} ${fmt(x - 5)} ${fmt(y + largo * 0.7)} ${fmt(x)} ${fmt(y + largo)}`;
  }
  const n = dias.length;
  // Con tallo, los pétalos se abren en abanico hacia arriba y le dejan lugar; sin tallo, en círculo.
  const paso = conTallo ? (n > 1 ? Math.min(72, 240 / (n - 1)) : 0) : 360 / Math.max(n, 1);
  const petalos = dias.map(({ dia, lugares, alcanceKm }, i) => {
    const grados = conTallo ? -90 + (i - (n - 1) / 2) * paso : -90 + i * paso;
    const largo = 16 + 24 * Math.min(1, Math.sqrt(alcanceKm / 40));
    const ancho = 0.2 + 0.045 * Math.min(lugares, 6);
    return { dia, d: petalo(centro, grados, largo, ancho) };
  });
  return { centro, tallo, petalos };
}

/** Una hoja de `desde` a `hasta`, con la panza a `ancho` veces su largo. Trazo SVG (la marca). */
export function hoja(desde: Plano, hasta: Plano, ancho = 0.32): string {
  const dx = hasta.x - desde.x;
  const dy = hasta.y - desde.y;
  const largo = Math.hypot(dx, dy) || 1;
  const nx = -dy / largo;
  const ny = dx / largo;
  const medio = { x: desde.x + dx / 2, y: desde.y + dy / 2 };
  const abre = largo * ancho;
  const a = { x: medio.x + nx * abre, y: medio.y + ny * abre };
  const b = { x: medio.x - nx * abre, y: medio.y - ny * abre };
  return `M${fmt(desde.x)} ${fmt(desde.y)} Q${fmt(a.x)} ${fmt(a.y)} ${fmt(hasta.x)} ${fmt(hasta.y)} Q${fmt(b.x)} ${fmt(b.y)} ${fmt(desde.x)} ${fmt(desde.y)} Z`;
}

// ── En el mapa, con longitud y latitud ─────────────────────────────────────────────

/** La envolvente convexa de unos puntos (cadena monótona de Andrew), sin repetir el primero. */
export function envolvente<T extends Plano>(puntos: readonly T[]): T[] {
  const orden = [...puntos].sort((a, b) => a.x - b.x || a.y - b.y);
  if (orden.length < 3) return orden;
  const giro = (o: Plano, a: Plano, b: Plano) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const mitad = (lista: T[]) => {
    const salida: T[] = [];
    for (const q of lista) {
      while (
        salida.length >= 2 &&
        giro(salida[salida.length - 2] as T, salida[salida.length - 1] as T, q) <= 0
      ) {
        salida.pop();
      }
      salida.push(q);
    }
    return salida.slice(0, -1);
  };
  return [...mitad(orden), ...mitad([...orden].reverse())];
}

/** Lo mínimo que el pétalo se aparta de sus lugares: unos 350 m, en grados. */
const HOLGURA_MINIMA = 0.0032;

/**
 * El pétalo de un día en el mapa, como anillo cerrado de longitud y latitud: la envolvente de la
 * base y sus lugares, con un margen redondo alrededor de cada uno. Así contiene a todos sus
 * lugares, aunque estén en fila o sea uno solo. null si el día no tiene lugares.
 */
export function petaloGeografico(base: Par | null, lugares: readonly Par[], lados = 16): Par[] | null {
  if (lugares.length === 0) return null;
  const todos = base ? [base, ...lugares] : [...lugares];
  // A la latitud del Perú un grado de longitud mide casi lo mismo que uno de latitud, pero no
  // igual: se corrige para que el pétalo no salga deformado.
  const c = Math.cos(((todos.reduce((s, p) => s + p[1], 0) / todos.length) * Math.PI) / 180);
  const planos = todos.map(([lon, lat]): Plano => ({ x: lon * c, y: lat }));
  const centro = planos[0] as Plano;
  const alcance = Math.max(...planos.map((p) => Math.hypot(p.x - centro.x, p.y - centro.y)));
  const holgura = Math.max(alcance * 0.12, HOLGURA_MINIMA);
  const alrededor = planos.flatMap((p) =>
    Array.from({ length: lados }, (_, k) => {
      const a = (2 * Math.PI * k) / lados;
      return { x: p.x + holgura * Math.cos(a), y: p.y + holgura * Math.sin(a) };
    }),
  );
  const anillo = envolvente(alrededor).map((p): Par => [p.x / c, p.y]);
  const primero = anillo[0];
  return primero ? [...anillo, primero] : null;
}
