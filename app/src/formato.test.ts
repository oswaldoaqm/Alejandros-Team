import { describe, expect, it } from "vitest";
import {
  aIso,
  decimal,
  duracion,
  fecha,
  fechaCorta,
  fechaLocal,
  fijo,
  horas,
  km,
  letra,
  lista,
  mes,
  metros,
  miles,
  plural,
  rangoDeFechas,
  rangosDeMeses,
  soles,
  solesExactos,
} from "./formato";

const nb = "\u00a0";

describe("números", () => {
  it("separa los miles con un espacio que no parte la línea", () => {
    expect(miles(1250)).toBe(`1${nb}250`);
    expect(miles(999)).toBe("999");
    expect(miles(1234567.4)).toBe(`1${nb}234${nb}567`);
    expect(soles(707)).toBe(`S/${nb}707`);
    expect(soles(1640)).toBe(`S/${nb}1${nb}640`);
    expect(metros(3256)).toBe(`3${nb}256${nb}m`);
  });

  it("usa la coma decimal y no escribe ceros de más", () => {
    expect(decimal(7.9)).toBe("7,9");
    expect(decimal(12)).toBe("12");
    expect(decimal(0.33, 2)).toBe("0,33");
    expect(decimal(1234.56)).toBe(`1${nb}234,6`);
  });

  it("escribe los km con un decimal solo cuando son pocos", () => {
    expect(km(8.8)).toBe(`8,8${nb}km`);
    expect(km(752.7)).toBe(`753${nb}km`);
  });

  it("concuerda el plural", () => {
    expect(plural(1, "parada", "paradas")).toBe(`1${nb}parada`);
    expect(plural(15, "parada", "paradas")).toBe(`15${nb}paradas`);
  });
});

describe("duraciones", () => {
  it("las escribe como el motor", () => {
    expect(duracion(45)).toBe(`45${nb}min`);
    expect(duracion(60)).toBe(`1${nb}h`);
    expect(duracion(160)).toBe(`2${nb}h${nb}40`);
    expect(duracion(125)).toBe(`2${nb}h${nb}05`);
    expect(horas(6.05)).toBe(`6${nb}h${nb}03`);
  });
});

describe("fechas", () => {
  it("lee AAAA-MM-DD como día local, sin correrse por la zona horaria", () => {
    const f = fechaLocal("2027-07-01");
    expect(f?.getDate()).toBe(1);
    expect(f?.getMonth()).toBe(6);
    expect(fechaLocal("ayer")).toBeNull();
    expect(aIso(new Date(2027, 0, 5))).toBe("2027-01-05");
  });

  it("escribe un día, un rango dentro del mes y un rango entre meses", () => {
    expect(rangoDeFechas("2027-07-16", "2027-07-16")).toBe("16 de julio");
    expect(rangoDeFechas("2027-07-24", "2027-07-30")).toBe("del 24 al 30 de julio");
    expect(rangoDeFechas("2026-12-28", "2027-01-06")).toBe("del 28 de diciembre al 6 de enero");
    expect(rangoDeFechas(null, null)).toBe("");
  });

  it("nombra los meses como el motor: setiembre", () => {
    expect(mes(9)).toBe("setiembre");
    expect(mes(13)).toBe("");
    expect(fecha("2027-09-20")).toBe("20 de setiembre de 2027");
    expect(fechaCorta("2027-07-20")).toBe("mar 20 jul");
  });
});

describe("listas y letras", () => {
  it("une con comas y una conjunción", () => {
    expect(lista(["a"])).toBe("a");
    expect(lista(["a", "b", "c"])).toBe("a, b y c");
    expect(lista(["tren", "bote"], "o")).toBe("tren o bote");
  });

  it("nombra las rutas A, B y C", () => {
    expect([0, 1, 2].map(letra)).toEqual(["A", "B", "C"]);
  });
});

describe("lo que se añadió para la app", () => {
  it("no redondea una tarifa", () => {
    expect(solesExactos(10)).toBe(`S/${nb}10`);
    expect(solesExactos(2.5)).toBe(`S/${nb}2,50`);
  });

  it("deja los decimales fijos cuando se comparan en columna", () => {
    expect(fijo(2)).toBe("2,0");
    expect(fijo(1.83)).toBe("1,8");
  });

  it("dice los meses como tramos del calendario, lleguen en el orden que lleguen", () => {
    expect(rangosDeMeses([6, 7, 8, 5, 9, 4, 10, 11])).toBe("de abril a noviembre");
    expect(rangosDeMeses([12, 1, 2])).toBe("de diciembre a febrero");
    expect(rangosDeMeses([8])).toBe("agosto");
    expect(rangosDeMeses([7, 6])).toBe("junio y julio");
    expect(rangosDeMeses([5, 6, 7, 10])).toBe("de mayo a julio y octubre");
    expect(rangosDeMeses([1, 2, 6, 7, 8, 12])).toBe("de junio a agosto y de diciembre a febrero");
    expect(rangosDeMeses([3, 4, 9])).toBe("marzo, abril y setiembre");
    expect(rangosDeMeses([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])).toBe("todo el año");
    expect(rangosDeMeses([])).toBe("");
  });
});
