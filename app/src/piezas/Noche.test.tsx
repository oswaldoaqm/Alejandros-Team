import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Noche } from "../api/tipos";
import { plano } from "../pruebas/texto";
import { FaseDeLuna, NocheDelDia } from "./Noche";

const SALIR: Noche = {
  tipo: "salir",
  titulo: "Salir en Cuzco",
  nota: "A no más de 23 minutos a pie de donde duermes hay 72 bares, 16 pubs y 11 discotecas.",
  lugares: [
    {
      nombre: "Paddy's Irish Pub",
      tipo: "pub",
      lat: -13.5168,
      lon: -71.9775,
      minutos_a_pie: 2,
      fuente: "openstreetmap",
      url: "https://www.openstreetmap.org/way/584934213",
      horario: "Mo-Su 15:00-23:00",
    },
    {
      nombre: "El Muki",
      tipo: "discoteca",
      lat: -13.517,
      lon: -71.9776,
      minutos_a_pie: 2,
      fuente: "overture",
      url: "https://www.openstreetmap.org/?mlat=-13.517056&mlon=-71.977615#map=19/-13.517056/-71.977615",
      horario: null,
    },
  ],
  cielo: null,
};

const ESTRELLAS: Noche = {
  tipo: "estrellas",
  titulo: "Noche de estrellas",
  nota: "Desde Mazo Cruz el cielo es muy oscuro: se ve la Vía Láctea de lado a lado.",
  lugares: [],
  cielo: {
    desde: {
      nombre: "Mazo Cruz",
      tipo: "base",
      minutos: 0,
      lat: -16.74,
      lon: -69.72,
      url: null,
      brillo: 0.17,
      clase: "muy_oscuro",
    },
    observatorio: null,
    noches_despejadas: 0.86,
    fuente_nubes: "goes",
    aeropuerto: null,
    oscurece: "18:50",
    aclara: "04:55",
    luna: { iluminada: 0.08, creciente: true, sale: null, se_pone: "19:40", horas_sin_luna: 9.2 },
    lunas_nuevas: [],
    temp_min_c: -6,
  },
};

describe("la noche de un día", () => {
  it("para salir: los lugares, con su tipo, a cuánto quedan y dónde verificarlos", () => {
    render(<NocheDelDia noche={SALIR} />);
    const noche = screen.getByRole("region", { name: "De noche: Salir en Cuzco" });
    expect(within(noche).getByRole("heading", { name: "Salir en Cuzco" })).toBeTruthy();
    const lista = within(noche).getByRole("list", { name: "Para esta noche" });
    const lugares = within(lista)
      .getAllByRole("listitem")
      .map((li) => plano(li.textContent));
    expect(lugares).toEqual(["Paddy's Irish Pub Pub · 2 min a pie", "El Muki Discoteca · 2 min a pie"]);
    expect(within(noche).getByRole("link", { name: "El Muki" }).getAttribute("href")).toContain(
      "mlat=-13.517056",
    );
    expect(plano(noche.textContent)).toContain("confirma que sigan abiertos");
  });

  it("para las estrellas: el cielo, la luna de esa noche y nada de bares", () => {
    render(<NocheDelDia noche={ESTRELLAS} />);
    const noche = screen.getByRole("region", { name: "De noche: Noche de estrellas" });
    const texto = plano(noche.textContent);
    expect(texto).toContain("Luna al 8 %");
    expect(texto).toContain("Cielo muy oscuro");
    expect(texto).toContain("Vía Láctea");
    expect(within(noche).queryByRole("list")).toBeNull();
  });
});

describe("la luna", () => {
  const dibujo = (iluminada: number, creciente: boolean) => {
    const { container, unmount } = render(<FaseDeLuna luna={{ iluminada, creciente }} />);
    const d = container.querySelector(".luna__luz")?.getAttribute("d") ?? null;
    unmount();
    return d;
  };

  it("en luna nueva no hay parte iluminada; en cuarto, la mitad, sin curva", () => {
    expect(dibujo(0, true)).toBeNull();
    expect(dibujo(0.5, true)).toBe("M12 3A9 9 0 0 0 12 21A0.00 9 0 0 0 12 3Z");
  });

  it("en el sur, la creciente se ilumina por la izquierda y la menguante por la derecha", () => {
    expect(dibujo(0.2, true)).toMatch(/^M12 3A9 9 0 0 0 12 21A5\.40 9 0 0 1 12 3Z$/);
    expect(dibujo(0.2, false)).toMatch(/^M12 3A9 9 0 0 1 12 21A5\.40 9 0 0 0 12 3Z$/);
    // Gibosa: la sombra se curva al revés.
    expect(dibujo(0.8, true)).toMatch(/A5\.40 9 0 0 0 12 3Z$/);
  });
});
