import { describe, expect, it } from "vitest";
import { abanico, esExcursion, filasDelDia, numerar, puntosDeMapa } from "./itinerario";
import { RESPUESTA } from "./pruebas/api";

const [ruta] = RESPUESTA.rutas;
if (!ruta) throw new Error("El ejemplo del contrato no trae rutas.");

describe("las paradas numeradas", () => {
  it("se numeran desde 1 en cada día, en el orden de visita", () => {
    const dias = numerar(ruta.dias);
    for (const { paradas } of dias) {
      expect(paradas.map((p) => p.numero)).toEqual(paradas.map((_, i) => i + 1));
      const ordenes = paradas.map((p) => p.parada.orden);
      expect(ordenes).toEqual([...ordenes].sort((a, b) => a - b));
    }
    expect(dias.flatMap((d) => d.paradas)).toHaveLength(ruta.indicadores.paradas);
  });

  it("el mapa recibe las mismas paradas, con su día, su número y su código", () => {
    const dias = numerar(ruta.dias);
    const puntos = puntosDeMapa(dias);
    expect(puntos.map((p) => `${p.dia}-${p.numero}`)).toEqual(
      dias.flatMap((d) => d.paradas.map((p) => `${d.dia.numero}-${p.numero}`)),
    );
    const primero = dias.find((d) => d.paradas.length > 0);
    expect(puntos[0]).toMatchObject({
      nombre: primero?.paradas[0]?.parada.recurso.nombre,
      codigo: primero?.paradas[0]?.parada.recurso.codigo,
      dia: primero?.dia.numero,
      numero: 1,
      hora: primero?.paradas[0]?.parada.llegada,
    });
  });

  it("un viaje de un día no tiene base", () => {
    expect(esExcursion(ruta)).toBe(false);
    expect(esExcursion({ dias: [{ numero: 1, tipo: "ida_visita_y_vuelta", horas: 7, km: 90 }] })).toBe(true);
  });
});

describe("el almuerzo entre los lugares del día", () => {
  it("va después de los lugares que van antes, y un día sin almuerzo tiene solo sus lugares", () => {
    const dias = RESPUESTA.rutas.flatMap((r) => numerar(r.dias));
    expect(dias.some((d) => d.dia.almuerzo)).toBe(true);
    for (const numerado of dias) {
      const filas = filasDelDia(numerado);
      const almuerzo = numerado.dia.almuerzo;
      expect(filas.filter((f) => f.tipo === "parada")).toHaveLength(numerado.paradas.length);
      if (!almuerzo) {
        expect(filas.some((f) => f.tipo === "almuerzo")).toBe(false);
        continue;
      }
      expect(filas.findIndex((f) => f.tipo === "almuerzo")).toBe(almuerzo.despues_de);
    }
  });

  it("si el número no cabe, va al final; y sin lugares no hay almuerzo que mostrar", () => {
    const almuerzo = {
      hora: "13:00",
      despues_de: 9,
      lugar: "Huaraz",
      en_la_base: true,
      hay_donde_comer: null,
    };
    const [conUno] = numerar([
      {
        numero: 1,
        tipo: "visita",
        horas: 1,
        km: 1,
        almuerzo,
        paradas: ruta.dias.flatMap((d) => d.paradas ?? []).slice(0, 1),
      },
    ]);
    if (!conUno) throw new Error("Falta el día.");
    expect(filasDelDia(conUno).map((f) => f.tipo)).toEqual(["parada", "almuerzo"]);
    expect(filasDelDia({ ...conUno, paradas: [] })).toEqual([]);
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
