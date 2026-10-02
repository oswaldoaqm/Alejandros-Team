// El itinerario con sus paradas numeradas de corrido en todo el viaje: el mismo número
// aparece en la lista y en el mapa.

import type { Dia, Parada, Ruta } from "./api/tipos";

export interface ParadaNumerada {
  numero: number;
  parada: Parada;
}

export interface DiaNumerado {
  dia: Dia;
  paradas: ParadaNumerada[];
}

export interface PuntoDeMapa {
  lat: number;
  lon: number;
  nombre: string;
  /** El número de la parada en todo el viaje, el mismo del itinerario. */
  numero: number;
  dia: number;
  hora: string;
}

export function numerar(dias: readonly Dia[]): DiaNumerado[] {
  let numero = 0;
  return dias.map((dia) => ({
    dia,
    paradas: [...(dia.paradas ?? [])]
      .sort((a, b) => a.orden - b.orden)
      .map((parada) => {
        numero += 1;
        return { numero, parada };
      }),
  }));
}

export function puntosDeMapa(dias: readonly DiaNumerado[]): PuntoDeMapa[] {
  return dias.flatMap(({ dia, paradas }) =>
    paradas.map(({ numero, parada }) => ({
      lat: parada.recurso.lat,
      lon: parada.recurso.lon,
      nombre: parada.recurso.nombre,
      numero,
      dia: dia.numero,
      hora: parada.llegada,
    })),
  );
}

/** Un viaje de ida y vuelta en el día: no se duerme en ninguna base. */
export function esExcursion(ruta: Pick<Ruta, "dias">): boolean {
  return ruta.dias.length === 1 && ruta.dias[0]?.tipo === "ida_visita_y_vuelta";
}

/**
 * En el mapa, las paradas que caen casi en el mismo punto de la pantalla se tapan (un museo
 * junto a su sitio arqueológico). Dadas sus posiciones en píxeles, dice cuánto correr cada
 * una hacia los lados, en anchos de marcador: 0 si está sola; −0,5 y +0,5 si son dos;
 * −1, 0 y +1 si son tres. Así todos los números quedan a la vista.
 *
 * Con `primeraFija`, la primera posición (la base) no se mueve: lo que se le encima se
 * abre hacia su derecha: 0, 1, 2…
 */
export function abanico(
  posiciones: readonly { x: number; y: number }[],
  juntos: number,
  primeraFija = false,
): number[] {
  const grupos: number[][] = [];
  posiciones.forEach((p, i) => {
    const grupo = grupos.find((g) => {
      const primera = posiciones[g[0] ?? 0];
      return primera !== undefined && Math.hypot(primera.x - p.x, primera.y - p.y) < juntos;
    });
    if (grupo) grupo.push(i);
    else grupos.push([i]);
  });
  const corrimiento = new Array<number>(posiciones.length).fill(0);
  for (const grupo of grupos) {
    const centro = primeraFija && grupo[0] === 0 ? 0 : (grupo.length - 1) / 2;
    grupo.forEach((i, puesto) => {
      corrimiento[i] = puesto - centro;
    });
  }
  return corrimiento;
}
