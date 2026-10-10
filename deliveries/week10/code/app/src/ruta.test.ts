import { describe, expect, it } from "vitest";
import { POR_DEFECTO } from "./consulta";
import { enlaces, vistaDe } from "./ruta";

const BASE = "https://oswaldoaqm.github.io/Alejandros-Team/";
const vista = (resto: string) => vistaDe(new URL(resto, BASE));
const JULIO = { ...POR_DEFECTO, mes: 7 };

describe("de la URL a la pantalla", () => {
  it("sin consulta, el formulario", () => {
    expect(vista("")).toEqual({ tipo: "inicio", consulta: null });
    expect(vista("?origen=cusco")).toEqual({ tipo: "inicio", consulta: null });
  });

  it("con mes o fecha, los tres viajes, con la versión del enlace; con #/ruta/N, ese viaje abierto", () => {
    expect(vista("?origen=lima&mes=7&dias=6&v=2026.10.2")).toEqual({
      tipo: "resultados",
      consulta: JULIO,
      version: "2026.10.2",
      ruta: null,
    });
    expect(vista("?mes=7#/ruta/3")).toMatchObject({ tipo: "resultados", ruta: 3, version: null });
    // Un viaje que no existe deja ver los tres.
    expect(vista("?mes=7#/ruta/9")).toMatchObject({ tipo: "resultados", ruta: null });
  });

  it("las demás pantallas van en el fragmento y conservan la consulta", () => {
    expect(vista("?mes=7#/editar")).toEqual({ tipo: "inicio", consulta: JULIO });
    expect(vista("?mes=7#/polo/33")).toEqual({ tipo: "polo", id: 33, consulta: JULIO });
    expect(vista("#/polo/0")).toEqual({ tipo: "polo", id: 0, consulta: null });
    expect(vista("#/calendario")).toEqual({ tipo: "calendario", consulta: null, mes: null });
    expect(vista("#/mis-viajes")).toEqual({ tipo: "mis-viajes" });
    expect(vista("#/acerca")).toEqual({ tipo: "acerca" });
    expect(vista("#/publicar")).toEqual({ tipo: "publicar" });
  });

  it("el calendario se puede abrir en un mes", () => {
    expect(vista("#/calendario/11")).toEqual({ tipo: "calendario", consulta: null, mes: 11 });
    expect(vista("?mes=7#/calendario/2")).toEqual({ tipo: "calendario", consulta: JULIO, mes: 2 });
    for (const otro of ["0", "13", "1.5", "noviembre"]) {
      expect(vista(`#/calendario/${otro}`)).toEqual({ tipo: "calendario", consulta: null, mes: null });
    }
  });

  it("un fragmento que no conoce no rompe nada", () => {
    expect(vista("#/polo/abc")).toEqual({ tipo: "inicio", consulta: null });
    expect(vista("?mes=7#/otra-cosa")).toMatchObject({ tipo: "resultados", ruta: null });
  });
});

describe("de la pantalla a la URL", () => {
  it("arma enlaces que vuelven a la misma pantalla", () => {
    expect(enlaces.resultados(JULIO, "2026.10.2", 2)).toBe("?origen=lima&mes=7&dias=6&v=2026.10.2#/ruta/2");
    expect(enlaces.resultados(JULIO, "2026.10.2")).toBe("?origen=lima&mes=7&dias=6&v=2026.10.2");
    expect(vista(enlaces.resultados(JULIO, "2026.10.2"))).toEqual({
      tipo: "resultados",
      consulta: JULIO,
      version: "2026.10.2",
      ruta: null,
    });
    expect(vista(enlaces.resultados(JULIO, "2026.10.2", 2))).toMatchObject({ tipo: "resultados", ruta: 2 });
    expect(vista(enlaces.editar(JULIO))).toEqual({ tipo: "inicio", consulta: JULIO });
    expect(vista(enlaces.polo(33, JULIO, "2026.10.2"))).toEqual({ tipo: "polo", id: 33, consulta: JULIO });
    expect(vista(enlaces.polo(33))).toEqual({ tipo: "polo", id: 33, consulta: null });
    expect(vista(enlaces.calendario())).toEqual({ tipo: "calendario", consulta: null, mes: null });
    expect(vista(enlaces.calendario(null, null, 11))).toEqual({
      tipo: "calendario",
      consulta: null,
      mes: 11,
    });
    expect(vista(enlaces.calendario(JULIO, "2026.10.2", 11))).toEqual({
      tipo: "calendario",
      consulta: JULIO,
      mes: 11,
    });
    expect(vista(enlaces.misViajes())).toEqual({ tipo: "mis-viajes" });
    expect(vista(enlaces.acerca())).toEqual({ tipo: "acerca" });
    expect(vista(enlaces.publicar())).toEqual({ tipo: "publicar" });
    expect(vista(enlaces.inicio())).toEqual({ tipo: "inicio", consulta: null });
  });
});
