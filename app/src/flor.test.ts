import { describe, expect, it } from "vitest";
import { diasDeLaFlor, envolvente, florDelViaje, kmEntre, petaloGeografico } from "./flor";

/** Si el punto cae dentro del polígono (o en su borde). */
function adentro([x, y]: [number, number], anillo: [number, number][]): boolean {
  let dentro = false;
  for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
    const [xi, yi] = anillo[i] as [number, number];
    const [xj, yj] = anillo[j] as [number, number];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) dentro = !dentro;
  }
  return dentro;
}

describe("la flor del viaje", () => {
  it("mide en línea recta: un grado de latitud son unos 111 km", () => {
    expect(kmEntre({ lat: -12, lon: -75 }, { lat: -13, lon: -75 })).toBeCloseTo(111.2, 0);
  });

  it("resume cada día con lugares: cuántos visita y hasta dónde llega desde donde se duerme", () => {
    const base = { lat: -12, lon: -75 };
    const dias = diasDeLaFlor(base, [
      { lat: -12.1, lon: -75, dia: 2 },
      { lat: -12, lon: -75.05, dia: 1 },
      { lat: -12.3, lon: -75, dia: 2 },
    ]);
    expect(dias.map((d) => [d.dia, d.lugares])).toEqual([
      [1, 1],
      [2, 2],
    ]);
    expect(dias[1]?.alcanceKm).toBeCloseTo(33.4, 0);
  });

  it("un pétalo por día, más largo el día que va más lejos", () => {
    const flor = florDelViaje([
      { dia: 1, lugares: 3, alcanceKm: 2 },
      { dia: 2, lugares: 3, alcanceKm: 40 },
    ]);
    expect(flor.petalos.map((p) => p.dia)).toEqual([1, 2]);
    expect(flor.tallo).toBeNull();
    // Todos salen de donde se duerme.
    for (const p of flor.petalos) expect(p.d.startsWith(`M${flor.centro.x} ${flor.centro.y} `)).toBe(true);
    const punta = (d: string) => {
      const numeros = d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [];
      // La punta es el último punto de la primera curva: los números 7 y 8 del trazo.
      return Math.hypot((numeros[6] ?? 0) - flor.centro.x, (numeros[7] ?? 0) - flor.centro.y);
    };
    const [corto, largo] = flor.petalos.map((p) => punta(p.d));
    expect(largo).toBeGreaterThan(corto ?? 0);
  });

  it("con la ida, un tallo que crece con las horas, hasta siete", () => {
    const largoDelTallo = (horas: number) => {
      const tallo = florDelViaje([{ dia: 1, lugares: 2, alcanceKm: 5 }], horas).tallo ?? "";
      const numeros = tallo.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [];
      return (numeros.at(-1) ?? 0) - (numeros[1] ?? 0);
    };
    expect(largoDelTallo(2)).toBeLessThan(largoDelTallo(6));
    expect(largoDelTallo(7)).toBe(largoDelTallo(12));
  });
});

describe("el pétalo de un día en el mapa", () => {
  it("la envolvente deja afuera lo que queda adentro", () => {
    const cuadrado = envolvente([
      { x: 0, y: 0 },
      { x: 2, y: 0 },
      { x: 1, y: 1 },
      { x: 2, y: 2 },
      { x: 0, y: 2 },
    ]);
    expect(cuadrado).toHaveLength(4);
    expect(cuadrado).not.toContainEqual({ x: 1, y: 1 });
  });

  it("contiene la base y todos los lugares del día, y es un anillo cerrado", () => {
    const base: [number, number] = [-75.21, -12.07];
    const lugares: [number, number][] = [
      [-75.3, -12.0],
      [-75.25, -12.15],
      [-75.1, -12.1],
    ];
    const anillo = petaloGeografico(base, lugares);
    if (!anillo) throw new Error("El día tiene lugares: debería tener pétalo.");
    expect(anillo[0]).toEqual(anillo.at(-1));
    for (const punto of [base, ...lugares]) expect(adentro(punto, anillo)).toBe(true);
  });

  it("con un solo lugar y sin base, es un círculo chico alrededor de él", () => {
    const lugar: [number, number] = [-77.03, -12.05];
    const anillo = petaloGeografico(null, [lugar]);
    if (!anillo) throw new Error("Debería tener pétalo.");
    expect(adentro(lugar, anillo)).toBe(true);
    const radio = Math.max(...anillo.map(([lon, lat]) => Math.hypot(lon - lugar[0], lat - lugar[1])));
    expect(radio).toBeLessThan(0.01);
  });

  it("un día sin lugares no tiene pétalo", () => {
    expect(petaloGeografico([-75, -12], [])).toBeNull();
  });
});
