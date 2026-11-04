import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { App } from "../App";
import { irA, ponerApi } from "../pruebas/api";

describe("pantalla de blog viajero", () => {
  it("muestra el catálogo general, lo más reciente y los filtros de categoría", async () => {
    irA("./#/blog");
    ponerApi();
    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "Blog viajero" })).toBeDefined();
    expect(screen.getByRole("heading", { level: 2, name: "Lo más reciente" })).toBeDefined();

    // Filtros
    expect(screen.getByRole("tab", { name: "Todos" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Gastronomía" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Festividades" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Aventura" })).toBeDefined();

    // Filtra por categoría Gastronomía en el feed general
    await userEvent.click(screen.getByRole("tab", { name: "Gastronomía" }));
    const feed = screen.getByRole("region", { name: "Listado de artículos del blog" });
    expect(within(feed).getByText("Postres peruanos: 12 dulces para recorrer el Perú")).toBeDefined();
    expect(
      within(feed).queryByText(
        "Festival Rural Tour Huayllay: vive dos días de naturaleza y tradición en Pasco",
      ),
    ).toBeNull();
  });

  it("permite abrir y leer una nota completa con sus consejos y CTA a Planear", async () => {
    irA("./#/blog/virgen-de-la-candelaria-puno");
    ponerApi();
    render(<App />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /Virgen de la Candelaria 2027: todo sobre su presentación oficial/i,
      }),
    ).toBeDefined();
    expect(screen.getByText("Lugares y paradas imperdibles")).toBeDefined();
    expect(screen.getByText("Consejos para tu visita")).toBeDefined();

    const btnPlanear = screen.getByRole("link", { name: /Planear viaje a este destino/i });
    expect(btnPlanear.getAttribute("href")).toBe("./#/planear");
  });
});
