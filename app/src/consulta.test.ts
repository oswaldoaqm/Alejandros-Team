import { describe, expect, it } from "vitest";
import {
  aEnlace,
  aParametros,
  type Consulta,
  clave,
  deParametros,
  POR_DEFECTO,
  piezas,
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
  it("la parte en piezas que se pueden quitar, menos el mes", () => {
    const lista = piezas(COMPLETA, NOMBRES);
    expect(lista.map((p) => p.texto)).toEqual([
      "Desde Cusco",
      `4${nb}días`,
      "Julio",
      "Historia y arqueología",
      "Playa",
      `Hasta S/${nb}1${nb}800`,
      `Hasta 2${nb}500${nb}m`,
      "Sorpréndeme",
    ]);
    expect(lista.find((p) => p.campo === "mes")?.sin).toBeNull();
    expect(lista.find((p) => p.valor === "playa")?.sin?.intereses).toEqual(["historia"]);
    expect(lista.find((p) => p.campo === "presupuesto")?.sin?.presupuesto).toBeNull();
    expect(lista.find((p) => p.campo === "origen")?.sin?.origen).toBe("lima");
  });

  it("no ofrece quitar lo que ya está en su valor por defecto", () => {
    const lista = piezas({ ...POR_DEFECTO, mes: 7 }, NOMBRES);
    expect(lista.map((p) => [p.texto, p.sin])).toEqual([
      ["Desde Lima", null],
      [`6${nb}días`, null],
      ["Julio", null],
    ]);
  });

  it("al quitar la fecha se queda con su mes", () => {
    const lista = piezas({ ...POR_DEFECTO, mes: 7, fecha_inicio: "2027-07-20" }, NOMBRES);
    const fecha = lista.find((p) => p.campo === "fecha_inicio");
    expect(fecha?.texto).toBe("Sale el 20 de julio");
    expect(fecha?.sin).toMatchObject({ fecha_inicio: null, mes: 7 });
  });

  it("le pone un título corto", () => {
    expect(titulo(COMPLETA, NOMBRES)).toBe(
      `Cusco · julio · 4${nb}días · historia y arqueología y playa · sorpréndeme`,
    );
    expect(titulo({ ...POR_DEFECTO, mes: 2 }, NOMBRES)).toBe(`Lima · febrero · 6${nb}días`);
  });
});
