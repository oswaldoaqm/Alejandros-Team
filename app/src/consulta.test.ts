import { describe, expect, it } from "vitest";
import {
  aEnlace,
  aParametros,
  type Consulta,
  clave,
  deParametros,
  detalles,
  POR_DEFECTO,
  titulo,
} from "./consulta";

const nb = "\u00a0"; // el espacio que no parte la línea

const NOMBRES = {
  origenes: { lima: "Lima", cusco: "Cusco" },
  intereses: { historia: "Historia y arqueología", playa: "Playa" },
};

const COMPLETA: Consulta = {
  origen: "cusco",
  mes: 7,
  fecha_inicio: null,
  dias: 4,
  intereses: ["historia", "playa"],
  presupuesto: 1800,
  altitud_max: 2500,
  sorpresa: true,
};

describe("la consulta y la URL", () => {
  it("escribe los parámetros que recibe GET /v1/viajes, en orden fijo", () => {
    expect(aParametros(COMPLETA).toString()).toBe(
      "origen=cusco&mes=7&dias=4&intereses=historia&intereses=playa&presupuesto=1800&altitud_max=2500&sorpresa=true",
    );
    expect(aParametros({ ...POR_DEFECTO, mes: 2 }).toString()).toBe("origen=lima&mes=2&dias=6");
  });

  it("con fecha de inicio no manda el mes: basta la fecha", () => {
    const p = aParametros({ ...POR_DEFECTO, mes: 7, fecha_inicio: "2027-07-20" });
    expect(p.get("fecha_inicio")).toBe("2027-07-20");
    expect(p.has("mes")).toBe(false);
  });

  it("vuelve de la URL a la misma consulta", () => {
    expect(deParametros(aParametros(COMPLETA))).toEqual(COMPLETA);
    const conFecha = { ...POR_DEFECTO, mes: 7, fecha_inicio: "2027-07-20" };
    expect(deParametros(aParametros(conFecha))).toEqual(conFecha);
  });

  it("sin mes ni fecha no hay consulta", () => {
    expect(deParametros(new URLSearchParams("origen=lima&dias=6"))).toBeNull();
    expect(deParametros(new URLSearchParams(""))).toBeNull();
  });

  it("completa con los valores por defecto y no repite intereses", () => {
    const c = deParametros(new URLSearchParams("mes=3&intereses=playa&intereses=playa&v=2026.10.2"));
    expect(c).toEqual({ ...POR_DEFECTO, mes: 3, intereses: ["playa"] });
  });

  it("deja pasar un valor fuera de rango: el API es quien lo rechaza y dice por qué", () => {
    expect(deParametros(new URLSearchParams("mes=7&dias=99"))?.dias).toBe(99);
    expect(deParametros(new URLSearchParams("mes=7&dias=muchos"))?.dias).toBe(POR_DEFECTO.dias);
  });

  it("el enlace para compartir lleva la versión de datos", () => {
    expect(aEnlace({ ...POR_DEFECTO, mes: 7 }, "2026.10.2")).toBe("?origen=lima&mes=7&dias=6&v=2026.10.2");
    expect(aEnlace({ ...POR_DEFECTO, mes: 7 })).toBe("?origen=lima&mes=7&dias=6");
  });

  it("dos consultas con los mismos intereses en otro orden son la misma", () => {
    expect(clave({ ...COMPLETA, intereses: ["playa", "historia"] })).toBe(clave(COMPLETA));
    expect(clave({ ...COMPLETA, dias: 5 })).not.toBe(clave(COMPLETA));
  });
});

describe("la consulta en palabras", () => {
  it("en una frase: desde dónde, cuántos días y cuándo", () => {
    expect(titulo(COMPLETA, NOMBRES)).toBe(`Desde Cusco, 4${nb}días en julio`);
    expect(titulo({ ...POR_DEFECTO, mes: 2 }, NOMBRES)).toBe(`Desde Lima, 6${nb}días en febrero`);
    expect(titulo({ ...POR_DEFECTO, mes: 7, fecha_inicio: "2027-07-20" }, NOMBRES)).toBe(
      `Desde Lima, 6${nb}días desde el 20 de julio`,
    );
  });

  it("antes de que lleguen los nombres, el origen sale de su identificador", () => {
    const sinNombres = { origenes: {}, intereses: {} };
    expect(titulo({ ...POR_DEFECTO, origen: "puerto-maldonado", mes: 2 }, sinNombres)).toBe(
      `Desde Puerto maldonado, 6${nb}días en febrero`,
    );
  });

  it("lo demás que pidió, solo si pidió algo", () => {
    expect(detalles(COMPLETA, NOMBRES)).toBe(
      `Historia y arqueología y Playa, hasta S/${nb}1${nb}800 por persona, hasta 2${nb}500${nb}m de altura, solo lugares poco turísticos`,
    );
    expect(detalles({ ...POR_DEFECTO, mes: 7 }, NOMBRES)).toBeNull();
  });
});
