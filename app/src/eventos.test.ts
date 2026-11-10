import { describe, expect, it } from "vitest";
import type { Evento } from "./api/tipos";
import { POR_DEFECTO } from "./consulta";
import { caeEn, diasDeEvento, eventosDelDia, viajeAlEvento } from "./eventos";

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

describe("ir a un evento", () => {
  const evento = (cambios: Partial<Evento>): Evento => ({
    id: "1",
    nombre: "Fiesta de la Virgen del Carmen",
    fecha_inicio: "2027-07-16",
    fecha_fin: "2027-07-18",
    precision_fecha: "exacta",
    distrito: "Paucartambo",
    provincia: "Paucartambo",
    region: "Cusco",
    fuente: "mincetur",
    polo: 36,
    ...cambios,
  });
  const base = { ...POR_DEFECTO, origen: "arequipa", mes: 2, dias: 4, sorpresa: true };
  const hoy = new Date(2026, 9, 16);

  it("va a su zona, saliendo la víspera, y lo demás queda como estaba", () => {
    expect(viajeAlEvento(evento({}), base, hoy)).toEqual({
      ...base,
      destino: 36,
      sorpresa: false,
      fecha_inicio: "2027-07-15",
      mes: 7,
    });
  });

  it("en un viaje de un día sale el mismo día, y nunca antes de hoy", () => {
    expect(viajeAlEvento(evento({}), { ...base, dias: 1 }, hoy)?.fecha_inicio).toBe("2027-07-16");
    const yaEmpezo = evento({ fecha_inicio: "2026-10-15", fecha_fin: "2026-10-18" });
    expect(viajeAlEvento(yaEmpezo, base, hoy)).toMatchObject({ fecha_inicio: "2026-10-16", mes: 10 });
    const manana = evento({ fecha_inicio: "2026-10-17", fecha_fin: "2026-10-17" });
    expect(viajeAlEvento(manana, base, hoy)?.fecha_inicio).toBe("2026-10-16");
  });

  it("a lo que dura más de una semana o está por confirmar se va en su mes, sin fecha", () => {
    const todoElMes = evento({ fecha_inicio: "2027-02-01", fecha_fin: "2027-02-28" });
    expect(viajeAlEvento(todoElMes, base, hoy)).toMatchObject({ fecha_inicio: null, mes: 2, destino: 36 });
    const porConfirmar = evento({ precision_fecha: "por_confirmar", fecha_inicio: "2027-03-10" });
    expect(viajeAlEvento(porConfirmar, base, hoy)).toMatchObject({ fecha_inicio: null, mes: 3 });
  });

  it("a lo largo que ya empezó se va en este mes, no en el suyo", () => {
    const desdeSetiembre = evento({ fecha_inicio: "2026-09-29", fecha_fin: "2026-11-30" });
    expect(viajeAlEvento(desdeSetiembre, base, hoy)).toMatchObject({ fecha_inicio: null, mes: 10 });
  });

  it("si ya terminó o no queda cerca de ninguna zona, no hay viaje", () => {
    const terminado = evento({ fecha_inicio: "2026-09-29", fecha_fin: "2026-10-05" });
    expect(viajeAlEvento(terminado, base, hoy)).toBeNull();
    expect(viajeAlEvento(evento({ polo: null }), base, hoy)).toBeNull();
    expect(viajeAlEvento(evento({ polo: undefined }), base, hoy)).toBeNull();
  });
});
