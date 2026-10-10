import { describe, expect, it } from "vitest";
import { borrarViaje, estaGuardado, guardarViaje, leerViajes, type ViajeGuardado } from "./almacen";
import { POR_DEFECTO } from "./consulta";

function viaje(mes: number, ruta = 1, guardado = "2026-10-01T10:00:00Z"): ViajeGuardado {
  return { consulta: { ...POR_DEFECTO, mes }, ruta, version: "2026.10.2", titulo: `Mes ${mes}`, guardado };
}

describe("guardados", () => {
  it("guarda, lista del más reciente al más antiguo y borra", () => {
    expect(leerViajes()).toEqual([]);
    expect(guardarViaje(viaje(7))).toBe(true);
    guardarViaje(viaje(2));
    expect(leerViajes().map((v) => v.titulo)).toEqual(["Mes 2", "Mes 7"]);
    expect(estaGuardado({ ...POR_DEFECTO, mes: 7 }, 1)).toBe(true);
    borrarViaje({ ...POR_DEFECTO, mes: 7 }, 1);
    expect(leerViajes().map((v) => v.titulo)).toEqual(["Mes 2"]);
    expect(estaGuardado({ ...POR_DEFECTO, mes: 7 }, 1)).toBe(false);
  });

  it("no repite un viaje: lo sube al principio con sus datos nuevos", () => {
    guardarViaje(viaje(7));
    guardarViaje(viaje(2));
    guardarViaje({ ...viaje(7), version: "2026.10.3" });
    const lista = leerViajes();
    expect(lista.map((v) => v.titulo)).toEqual(["Mes 7", "Mes 2"]);
    expect(lista[0]?.version).toBe("2026.10.3");
  });

  it("guarda el viaje que se abrió, no la consulta: dos viajes de la misma consulta son dos guardados", () => {
    const julio = { ...POR_DEFECTO, mes: 7 };
    guardarViaje({ ...viaje(7, 1), titulo: "Huancayo" });
    expect(estaGuardado(julio, 1)).toBe(true);
    expect(estaGuardado(julio, 2)).toBe(false);

    guardarViaje({ ...viaje(7, 2), titulo: "La Merced" });
    expect(leerViajes().map((v) => [v.titulo, v.ruta])).toEqual([
      ["La Merced", 2],
      ["Huancayo", 1],
    ]);

    borrarViaje(julio, 1);
    expect(leerViajes().map((v) => v.titulo)).toEqual(["La Merced"]);
    expect(estaGuardado(julio, 2)).toBe(true);
  });

  it("lo guardado cuando los tres viajes iban en una pantalla se lee como la consulta entera", () => {
    const { ruta: _, ...deAntes } = viaje(7);
    localStorage.setItem(
      "dreemgo.viajes.v1",
      JSON.stringify([deAntes, { ...viaje(2), ruta: 9 }, { ...viaje(3), ruta: "2" }, viaje(4, 3)]),
    );
    expect(leerViajes().map((v) => [v.titulo, v.ruta])).toEqual([
      ["Mes 7", null],
      ["Mes 2", null],
      ["Mes 3", null],
      ["Mes 4", 3],
    ]);
    expect(estaGuardado({ ...POR_DEFECTO, mes: 7 }, null)).toBe(true);
    expect(estaGuardado({ ...POR_DEFECTO, mes: 7 }, 1)).toBe(false);
    borrarViaje({ ...POR_DEFECTO, mes: 7 }, null);
    expect(leerViajes().map((v) => v.titulo)).toEqual(["Mes 2", "Mes 3", "Mes 4"]);
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
