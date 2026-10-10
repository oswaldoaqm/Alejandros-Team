import { describe, expect, it } from "vitest";
import { caeEn, diasDeEvento, eventosDelDia } from "./eventos";

const FIESTA = { nombre: "Fiesta", fecha_inicio: "2027-07-16", fecha_fin: "2027-07-16" };
const FERIA = { nombre: "Feria", fecha_inicio: "2027-07-24", fecha_fin: "2027-07-26" };
const TODO_EL_MES = { nombre: "Concurso", fecha_inicio: "2027-07-01", fecha_fin: "2027-07-31" };
const SIN_FECHA = { nombre: "Por confirmar", fecha_inicio: null, fecha_fin: null };

describe("cuánto dura un evento", () => {
  it("cuenta los días, con el primero y el último", () => {
    expect(diasDeEvento(FIESTA)).toBe(1);
    expect(diasDeEvento(FERIA)).toBe(3);
    expect(diasDeEvento(TODO_EL_MES)).toBe(31);
    expect(diasDeEvento({ fecha_inicio: "2027-12-28", fecha_fin: "2028-01-06" })).toBe(10);
    expect(diasDeEvento({ fecha_inicio: "2027-07-16" })).toBe(1);
    expect(diasDeEvento(SIN_FECHA)).toBeNull();
  });
});

describe("en qué día del viaje cae", () => {
  it("cae entre su inicio y su fin", () => {
    expect(caeEn(FERIA, "2027-07-24")).toBe(true);
    expect(caeEn(FERIA, "2027-07-26")).toBe(true);
    expect(caeEn(FERIA, "2027-07-27")).toBe(false);
    expect(caeEn(SIN_FECHA, "2027-07-27")).toBe(false);
  });

  it("en el día se anotan los eventos cortos; el que dura todo el mes va aparte", () => {
    const todos = [FIESTA, FERIA, TODO_EL_MES, SIN_FECHA];
    expect(eventosDelDia(todos, "2027-07-16").map((e) => e.nombre)).toEqual(["Fiesta"]);
    expect(eventosDelDia(todos, "2027-07-25").map((e) => e.nombre)).toEqual(["Feria"]);
    expect(eventosDelDia(todos, "2027-07-10")).toEqual([]);
    expect(eventosDelDia(todos, null)).toEqual([]);
  });
});
