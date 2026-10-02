import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Dia, Evento, Recurso } from "../api/tipos";
import { numerar } from "../itinerario";
import { plano } from "../pruebas/texto";
import { Itinerario } from "./Itinerario";

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
  },
  {
    numero: 3,
    fecha: "2027-07-22",
    tipo: "visita_y_vuelta",
    horas: 7.7,
    km: 315.3,
    nota: "Vuelta a Lima: 6 h 03 por carretera.",
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

function pintar(verEnMapa = vi.fn()) {
  render(<Itinerario dias={numerar(DIAS)} eventos={EVENTOS} desde="Huancayo" verEnMapa={verEnMapa} />);
  return {
    verEnMapa,
    dias: screen.getAllByRole("heading", { level: 4 }).map((h) => h.closest("li") as HTMLElement),
  };
}

describe("el itinerario", () => {
  it("pone cada día con su fecha, lo que se hace y su jornada", () => {
    const { dias } = pintar();
    expect(dias).toHaveLength(3);
    expect(plano(dias[0]?.textContent)).toContain("Día 1mar 20 julIda y visitas");
    expect(plano(dias[0]?.textContent)).toContain("7 h 54 · 308 km");
    expect(plano(dias[1]?.textContent)).toContain("Día libre");
    expect(plano(dias[1]?.textContent)).not.toContain("0 min");
  });

  it("numera las paradas de corrido y dice desde dónde se llega a cada una", () => {
    const { dias } = pintar();
    const [primera, segunda] = within(dias[0] as HTMLElement).getAllByRole("listitem");
    expect(plano(primera?.textContent)).toContain("Parada 1, a las 13:11Capilla de la Merced");
    expect(plano(primera?.textContent)).toContain("A 8 min de Huancayo (0,6 km) · visita de 25 min");
    expect(plano(primera?.textContent)).toContain("Capilla · 3 250 m · Entrada libre");
    expect(plano(segunda?.textContent)).toContain("A 10 min de la anterior (2,5 km) · visita de 1 h");
    expect(plano(within(dias[2] as HTMLElement).getByRole("listitem").textContent)).toContain(
      "Parada 3, a las 09:00",
    );
  });

  it("cada parada enlaza a su ficha oficial, y dice cuando MINCETUR no la jerarquizó", () => {
    const { dias } = pintar();
    const fichas = screen.getAllByRole("link", { name: /Ficha oficial/ });
    expect(fichas.map((a) => a.getAttribute("href"))).toEqual(
      DIAS.flatMap((d) => (d.paradas ?? []).map((p) => p.recurso.url_ficha)),
    );
    expect(fichas.every((a) => a.getAttribute("rel")?.includes("noopener"))).toBe(true);
    expect(within(dias[0] as HTMLElement).getByText("Sin jerarquía")).toBeDefined();
    // Sin descripción en la ficha no se ofrece «Qué es».
    expect(within(dias[0] as HTMLElement).getAllByText("Qué es")).toHaveLength(1);
  });

  it("anota en su día el evento corto; el que dura todo el mes no", () => {
    const { dias } = pintar();
    expect(plano(dias[2]?.textContent)).toContain(
      "Ese día: Fiesta de Santiago, en Sicaya (fecha aproximada).",
    );
    expect(screen.queryByText(/Concurso de todo el mes/)).toBeNull();
  });

  it("el evento que publicó un municipio dice quién lo publicó", () => {
    const { dias } = pintar();
    expect(plano(dias[0]?.textContent)).toContain(
      "Ese día: Feria del Queso, en Concepción (publicado por Municipalidad Provincial de Concepción).",
    );
  });

  it("ofrece ver en el mapa los días que tienen paradas", async () => {
    const { verEnMapa } = pintar();
    const botones = screen.getAllByRole("button", { name: /en el mapa/ });
    expect(botones.map((b) => b.textContent)).toEqual(["Ver el día 1 en el mapa", "Ver el día 3 en el mapa"]);
    await userEvent.click(botones[1] as HTMLElement);
    expect(verEnMapa).toHaveBeenCalledWith(3);
  });
});
