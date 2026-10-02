import { describe, expect, it } from "vitest";
import { borrarViaje, estaGuardado, guardarViaje, leerViajes, type ViajeGuardado } from "./almacen";
import { POR_DEFECTO } from "./consulta";

function viaje(mes: number, guardado = "2026-10-01T10:00:00Z"): ViajeGuardado {
  return { consulta: { ...POR_DEFECTO, mes }, version: "2026.10.2", titulo: `Mes ${mes}`, guardado };
}

describe("mis viajes", () => {
  it("guarda, lista del más reciente al más antiguo y borra", () => {
    expect(leerViajes()).toEqual([]);
    expect(guardarViaje(viaje(7))).toBe(true);
    guardarViaje(viaje(2));
    expect(leerViajes().map((v) => v.titulo)).toEqual(["Mes 2", "Mes 7"]);
    expect(estaGuardado({ ...POR_DEFECTO, mes: 7 })).toBe(true);
    borrarViaje({ ...POR_DEFECTO, mes: 7 });
    expect(leerViajes().map((v) => v.titulo)).toEqual(["Mes 2"]);
    expect(estaGuardado({ ...POR_DEFECTO, mes: 7 })).toBe(false);
  });

  it("no repite un viaje: lo sube al principio con sus datos nuevos", () => {
    guardarViaje(viaje(7));
    guardarViaje(viaje(2));
    guardarViaje({ ...viaje(7), version: "2026.10.3" });
    const lista = leerViajes();
    expect(lista.map((v) => v.titulo)).toEqual(["Mes 7", "Mes 2"]);
    expect(lista[0]?.version).toBe("2026.10.3");
  });

  it("si lo guardado está roto, empieza de cero en vez de fallar", () => {
    localStorage.setItem("dreemgo.viajes.v1", "{no es json");
    expect(leerViajes()).toEqual([]);
    localStorage.setItem("dreemgo.viajes.v1", JSON.stringify([{ otra: "cosa" }, viaje(3)]));
    expect(leerViajes().map((v) => v.titulo)).toEqual(["Mes 3"]);
  });

  it("no guarda más de treinta", () => {
    for (let dias = 1; dias <= 14; dias++) {
      for (let mes = 1; mes <= 3; mes++)
        guardarViaje({ ...viaje(mes), consulta: { ...POR_DEFECTO, mes, dias } });
    }
    expect(leerViajes()).toHaveLength(30);
  });
});
