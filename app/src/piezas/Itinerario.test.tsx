import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Dia, Evento, Recurso } from "../api/tipos";
import type { Foto } from "../fotos";
import { numerar } from "../itinerario";
import { plano } from "../pruebas/texto";
import { HojaDeLugar, Itinerario, type LugarAbierto, SelectorDeDias } from "./Itinerario";

function recurso(codigo: string, nombre: string, extra: Partial<Recurso> = {}): Recurso {
  return {
    codigo,
    nombre,
    categoria: "Manifestaciones culturales",
    tipo: "Museos y otros",
    subtipo: "Museos",
    jerarquia: 2,
    lat: -12,
    lon: -75,
    altitud_m: 3250,
    ingreso: "pagado",
    tarifa_soles: 5,
    descripcion: `Qué es ${nombre}.`,
    url_ficha: `https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=${codigo}`,
    ...extra,
  };
}

const DIAS: Dia[] = [
  {
    numero: 1,
    fecha: "2027-07-20",
    tipo: "ida_y_visita",
    horas: 7.9,
    km: 307.7,
    nota: "Salida de Lima a las 07:00; 6 h 03 por carretera hasta Huancayo.",
    tranquilo: false,
    paradas: [
      {
        orden: 1,
        llegada: "13:11",
        minutos_traslado: 8,
        minutos_visita: 25,
        km_desde_anterior: 0.6,
        recurso: recurso("1", "Capilla de la Merced", {
          ingreso: "libre",
          tarifa_soles: 0,
          subtipo: "Capilla",
        }),
      },
      {
        orden: 2,
        llegada: "13:46",
        minutos_traslado: 10,
        minutos_visita: 60,
        km_desde_anterior: 2.5,
        recurso: recurso("2", "Lugar de la Memoria", { jerarquia: null, descripcion: null }),
      },
    ],
  },
  {
    numero: 2,
    fecha: "2027-07-21",
    tipo: "visita",
    horas: 0,
    km: 0,
    nota: "Día libre en Huancayo.",
    paradas: [],
    tranquilo: false,
  },
  {
    numero: 3,
    fecha: "2027-07-22",
    tipo: "visita_y_vuelta",
    horas: 7.7,
    km: 315.3,
    nota: "Vuelta a Lima: 6 h 03 por carretera.",
    tranquilo: false,
    paradas: [
      {
        orden: 1,
        llegada: "09:00",
        minutos_traslado: 7,
        minutos_visita: 20,
        km_desde_anterior: 0.1,
        recurso: recurso("3", "Catedral de Huancayo"),
      },
    ],
  },
];

const EVENTOS: Evento[] = [
  {
    id: "e1",
    nombre: "Fiesta de Santiago",
    fecha_inicio: "2027-07-22",
    fecha_fin: "2027-07-22",
    precision_fecha: "aproximada",
    distrito: "Sicaya",
    provincia: "Huancayo",
    region: "Junín",
    fuente: "mincetur",
    url: "https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=99",
  },
  {
    id: "e2",
    nombre: "Concurso de todo el mes",
    fecha_inicio: "2027-07-01",
    fecha_fin: "2027-07-31",
    precision_fecha: "aproximada",
    distrito: "Muqui",
    provincia: "Jauja",
    region: "Junín",
    fuente: "mincetur",
  },
  {
    id: "p-0123456789ab",
    nombre: "Feria del Queso",
    fecha_inicio: "2027-07-20",
    fecha_fin: "2027-07-21",
    precision_fecha: "exacta",
    distrito: "Concepción",
    provincia: "Concepción",
    region: "Junín",
    fuente: "publicado",
    publicado_por: "Municipalidad Provincial de Concepción",
  },
];

function pintar(dia: number | null, dias: Dia[] = DIAS) {
  const elegirDia = vi.fn();
  const abrirLugar = vi.fn();
  render(
    <Itinerario
      dias={numerar(dias)}
      eventos={EVENTOS}
      dia={dia}
      elegirDia={elegirDia}
      abrirLugar={abrirLugar}
    />,
  );
  return { elegirDia, abrirLugar };
}

describe("todo el viaje", () => {
  it("lista los días con su fecha, lo que se hace y sus lugares, o su nota si no tiene", () => {
    pintar(null);
    const dias = screen.getAllByRole("button");
    expect(dias.map((d) => plano(d.textContent))).toEqual([
      "Día 1 mar 20 jul Ida y visitas Capilla de la Merced y Lugar de la Memoria",
      "Día 2 mié 21 jul Día libre Día libre en Huancayo.",
      "Día 3 jue 22 jul Visitas y vuelta Catedral de Huancayo",
    ]);
  });

  it("al tocar un día, lo elige", async () => {
    const { elegirDia } = pintar(null);
    await userEvent.click(screen.getByRole("button", { name: /Día 3/ }));
    expect(elegirDia).toHaveBeenCalledWith(3);
  });
});

describe("la noche", () => {
  const CON_NOCHE: Dia[] = DIAS.map((d) =>
    d.numero === 2
      ? {
          ...d,
          noche: {
            tipo: "salir",
            titulo: "Salir en Huancayo",
            nota: "A no más de 20 minutos a pie de donde duermes hay 12 bares.",
            lugares: [
              {
                nombre: "Bar del Valle",
                tipo: "bar",
                lat: -12.06,
                lon: -75.2,
                minutos_a_pie: 5,
                fuente: "openstreetmap",
                url: "https://www.openstreetmap.org/node/7",
                horario: null,
              },
            ],
            cielo: null,
          },
        }
      : d,
  );

  it("en la lista, una línea bajo lo del día", () => {
    pintar(null, CON_NOCHE);
    expect(plano(screen.getByRole("button", { name: /Día 2/ }).textContent)).toBe(
      "Día 2 mié 21 jul Día libre Día libre en Huancayo. De noche: Salir en Huancayo",
    );
  });

  it("en el día, después de sus lugares, con dónde salir", () => {
    pintar(2, CON_NOCHE);
    const noche = screen.getByRole("region", { name: "De noche: Salir en Huancayo" });
    expect(within(noche).getByRole("link", { name: "Bar del Valle" })).toBeTruthy();
  });
});

describe("un día", () => {
  it("dice qué se hace, cuánto dura la jornada y cómo se llega", () => {
    pintar(1);
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("Día 1 mar 20 jul");
    expect(plano(screen.getByText(/Ida y visitas/).textContent)).toBe(
      "Ida y visitas: 7 h 54 de jornada y 308 km de camino.",
    );
    expect(screen.getByText(/Salida de Lima/).textContent).toBe(DIAS[0]?.nota);
  });

  it("pone sus lugares en orden, numerados desde 1, con la hora de llegada y la visita", () => {
    pintar(3);
    const [catedral] = within(screen.getByRole("list")).getAllByRole("button");
    // El número se ve en el círculo; el lector de pantalla no lo lee: ya va en el orden de la lista.
    expect(plano(catedral?.textContent)).toBe("09:00 1Catedral de Huancayo Visita de 20 min");
  });

  it("marca los imperdibles", () => {
    const conImperdible = DIAS.map((d) =>
      d.numero === 1
        ? {
            ...d,
            paradas: (d.paradas ?? []).map((p, i) =>
              i === 0 ? { ...p, recurso: { ...p.recurso, jerarquia: 3 } } : p,
            ),
          }
        : d,
    );
    render(
      <Itinerario
        dias={numerar(conImperdible)}
        eventos={[]}
        dia={1}
        elegirDia={vi.fn()}
        abrirLugar={vi.fn()}
      />,
    );
    const [capilla, memoria] = within(screen.getByRole("list")).getAllByRole("button");
    expect(plano(capilla?.textContent)).toContain("Imperdible");
    expect(plano(memoria?.textContent)).not.toContain("Imperdible");
  });

  it("al tocar un lugar, abre su hoja", async () => {
    const { abrirLugar } = pintar(1);
    await userEvent.click(screen.getByRole("button", { name: /Lugar de la Memoria/ }));
    expect(abrirLugar).toHaveBeenCalledWith(1, "2");
  });

  it("anota en su día el evento corto; el que dura todo el mes no", () => {
    pintar(3);
    expect(plano(screen.getByText(/Ese día/).textContent)).toBe(
      "Ese día: Fiesta de Santiago, en Sicaya (fecha aproximada).",
    );
    expect(screen.queryByText(/Concurso de todo el mes/)).toBeNull();
  });

  it("el evento que publicó un municipio dice quién lo publicó", () => {
    pintar(1);
    expect(plano(screen.getByText(/Ese día/).textContent)).toBe(
      "Ese día: Feria del Queso, en Concepción (publicado por Municipalidad Provincial de Concepción).",
    );
  });

  it("un día sin lugares muestra su nota", () => {
    pintar(2);
    expect(screen.getByText("Día libre en Huancayo.")).toBeDefined();
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("al final ofrece el día siguiente y, en el último, todo el viaje", async () => {
    const primero = pintar(1);
    await userEvent.click(screen.getByRole("button", { name: "Ver el día 2" }));
    expect(primero.elegirDia).toHaveBeenCalledWith(2);
  });

  it("en el último día ofrece volver a todo el viaje", async () => {
    const { elegirDia } = pintar(3);
    await userEvent.click(screen.getByRole("button", { name: "Ver todo el viaje" }));
    expect(elegirDia).toHaveBeenCalledWith(null);
  });
});

describe("el almuerzo", () => {
  const conAlmuerzo = (almuerzo: Dia["almuerzo"]): Dia[] =>
    DIAS.map((d) => (d.numero === 1 ? { ...d, almuerzo } : d));

  it("va en la línea del día, después de los lugares que van antes, sin número y sin abrirse", () => {
    pintar(
      1,
      conAlmuerzo({
        hora: "13:45",
        despues_de: 1,
        lugar: "Lugar de la Memoria",
        en_la_base: false,
        hay_donde_comer: true,
      }),
    );
    const filas = within(screen.getByRole("list", { name: "Lugares del día 1" })).getAllByRole("listitem");
    expect(filas.map((f) => plano(f.textContent))).toEqual([
      "13:11 1Capilla de la Merced Visita de 25 min",
      "13:45 Almuerzo Cerca de Lugar de la Memoria",
      "13:46 2Lugar de la Memoria Visita de 1 h",
    ]);
    expect(within(filas[1] as HTMLElement).queryByRole("button")).toBeNull();
    // Las horas del día no cuentan el almuerzo: el resumen lo dice.
    expect(plano(screen.getByText(/Ida y visitas/).textContent)).toBe(
      "Ida y visitas: 7 h 54 de jornada, más el almuerzo, y 308 km de camino.",
    );
  });

  it("si cerca no hay registrado dónde comer, dice que lo lleves", () => {
    pintar(
      1,
      conAlmuerzo({
        hora: "14:46",
        despues_de: 2,
        lugar: "Lugar de la Memoria",
        en_la_base: false,
        hay_donde_comer: false,
      }),
    );
    const filas = within(screen.getByRole("list", { name: "Lugares del día 1" })).getAllByRole("listitem");
    expect(plano(filas[2]?.textContent)).toBe(
      "14:46 Almuerzo En Lugar de la Memoria Lleva tu almuerzo: no tenemos registrado dónde comer cerca.",
    );
  });

  it("en la base, antes de salir", () => {
    pintar(
      1,
      conAlmuerzo({
        hora: "12:30",
        despues_de: 0,
        lugar: "Huancayo",
        en_la_base: true,
        hay_donde_comer: null,
      }),
    );
    const [primera] = within(screen.getByRole("list", { name: "Lugares del día 1" })).getAllByRole(
      "listitem",
    );
    expect(plano(primera?.textContent)).toBe("12:30 Almuerzo En Huancayo");
  });
});

describe("el selector de días", () => {
  it("ofrece todo el viaje y cada día, y marca el elegido", async () => {
    const elegirDia = vi.fn();
    render(<SelectorDeDias dias={[1, 2, 3]} dia={2} elegirDia={elegirDia} />);
    const opciones = screen.getAllByRole("radio");
    expect(opciones.map((o) => o.parentElement?.textContent)).toEqual(["Todo", "Día 1", "Día 2", "Día 3"]);
    expect(screen.getByRole("radio", { name: "Día 2" })).toHaveProperty("checked", true);
    await userEvent.click(screen.getByRole("radio", { name: "Todo" }));
    expect(elegirDia).toHaveBeenCalledWith(null);
  });
});

describe("la hoja de un lugar", () => {
  const [capilla, memoria] = DIAS[0]?.paradas ?? [];
  if (!capilla || !memoria) throw new Error("Faltan las paradas del primer día.");
  const abrir = (lugar: LugarAbierto | null) => {
    const alCerrar = vi.fn();
    render(<HojaDeLugar lugar={lugar} alCerrar={alCerrar} />);
    return alCerrar;
  };

  it("dice cuándo se llega, cuánto dura la visita, desde dónde, la altura, la entrada y su importancia", () => {
    abrir({ parada: capilla, numero: 1, dia: 1, desde: "Huancayo", foto: null });
    const hoja = screen.getByRole("dialog", { name: "Capilla de la Merced" });
    const filas = within(hoja)
      .getAllByRole("term")
      .map((t) => plano(`${t.textContent}: ${t.nextElementSibling?.textContent}`));
    expect(filas).toEqual([
      "Llegas: 13:11, día 1",
      "Visita: 25 min",
      "Desde Huancayo: 8 min, 0,6 km",
      "Altura: 3 250 m",
      "Entrada: Libre",
      "Importancia: 2 de 4, según MINCETUR",
    ]);
    expect(within(hoja).getByText("Qué es Capilla de la Merced.")).toBeDefined();
  });

  it("enlaza la ficha oficial, y dice si MINCETUR no calificó el lugar", () => {
    abrir({ parada: memoria, numero: 2, dia: 1, desde: "Capilla de la Merced", foto: null });
    const hoja = screen.getByRole("dialog", { name: "Lugar de la Memoria" });
    expect(within(hoja).getByText("MINCETUR no la ha calificado")).toBeDefined();
    const entrada = within(hoja).getByText("Entrada").nextElementSibling;
    expect(plano(entrada?.textContent)).toBe("S/ 5");
    const ficha = within(hoja).getByRole("link", { name: /Ver la ficha oficial/ });
    expect(ficha.getAttribute("href")).toBe(memoria?.recurso.url_ficha);
    expect(ficha.getAttribute("rel")).toContain("noopener");
  });

  it("con foto, la muestra con su autor y su licencia", () => {
    const foto: Foto = {
      archivo: "Capilla de la Merced (Huancayo).jpg",
      ruta: "a/ab",
      ancho: 2000,
      alto: 1500,
      autor: "Ana Quispe",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "Q1",
    };
    abrir({ parada: capilla, numero: 1, dia: 1, desde: "Huancayo", foto });
    const hoja = screen.getByRole("dialog");
    expect(within(hoja).getByRole("img", { name: "Capilla de la Merced" })).toBeDefined();
    expect(
      within(hoja)
        .getByRole("link", { name: /Foto: Ana Quispe/ })
        .getAttribute("href"),
    ).toBe("https://commons.wikimedia.org/wiki/File:Capilla_de_la_Merced_(Huancayo).jpg");
    expect(within(hoja).getByRole("link", { name: "CC BY-SA 4.0" })).toBeDefined();
  });

  it("cerrada no muestra nada, y la cruz la cierra", async () => {
    abrir(null);
    expect(screen.queryByRole("dialog")).toBeNull();
    const alCerrar = abrir({ parada: capilla, numero: 1, dia: 1, desde: "Huancayo", foto: null });
    await userEvent.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(alCerrar).toHaveBeenCalled();
  });
});
