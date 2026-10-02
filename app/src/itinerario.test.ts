import { describe, expect, it } from "vitest";
import { abanico, esExcursion, numerar, puntosDeMapa } from "./itinerario";
import { RESPUESTA } from "./pruebas/api";

const [ruta] = RESPUESTA.rutas;
if (!ruta) throw new Error("El ejemplo del contrato no trae rutas.");

describe("las paradas numeradas", () => {
  it("se numeran de corrido en todo el viaje, en el orden de cada día", () => {
    const dias = numerar(ruta.dias);
    const numeros = dias.flatMap((d) => d.paradas.map((p) => p.numero));
    expect(numeros).toEqual(numeros.map((_, i) => i + 1));
    expect(numeros).toHaveLength(ruta.indicadores.paradas);
    for (const { paradas } of dias) {
      const ordenes = paradas.map((p) => p.parada.orden);
      expect(ordenes).toEqual([...ordenes].sort((a, b) => a - b));
    }
  });

  it("el mapa recibe las mismas paradas con el mismo número", () => {
    const dias = numerar(ruta.dias);
    const puntos = puntosDeMapa(dias);
    expect(puntos.map((p) => p.numero)).toEqual(dias.flatMap((d) => d.paradas.map((p) => p.numero)));
    const primero = dias.find((d) => d.paradas.length > 0);
    expect(puntos[0]).toMatchObject({
      nombre: primero?.paradas[0]?.parada.recurso.nombre,
      dia: primero?.dia.numero,
      hora: primero?.paradas[0]?.parada.llegada,
    });
  });

  it("un viaje de un día no tiene base", () => {
    expect(esExcursion(ruta)).toBe(false);
    expect(esExcursion({ dias: [{ numero: 1, tipo: "ida_visita_y_vuelta", horas: 7, km: 90 }] })).toBe(true);
  });
});

describe("los marcadores que se tapan", () => {
  const SOLO = { x: 300, y: 300 };

  it("los que están lejos no se mueven", () => {
    expect(abanico([{ x: 0, y: 0 }, { x: 100, y: 0 }, SOLO], 24)).toEqual([0, 0, 0]);
  });

  it("dos juntos se abren medio paso a cada lado, y tres, uno entero", () => {
    expect(abanico([{ x: 0, y: 0 }, { x: 5, y: 3 }, SOLO], 24)).toEqual([-0.5, 0.5, 0]);
    expect(abanico([{ x: 0, y: 0 }, SOLO, { x: 5, y: 3 }, { x: 2, y: 2 }], 24)).toEqual([-1, 0, 0, 1]);
  });

  it("la base no se mueve: lo que se le encima se abre hacia su derecha", () => {
    expect(abanico([{ x: 0, y: 0 }, { x: 5, y: 3 }, { x: 1, y: 1 }, SOLO], 24, true)).toEqual([0, 1, 2, 0]);
    // Los grupos que no tocan la base se siguen abriendo a los dos lados.
    expect(abanico([{ x: 0, y: 0 }, SOLO, { x: 302, y: 300 }], 24, true)).toEqual([0, -0.5, 0.5]);
  });
});
