import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InsigniaJerarquia } from "./InsigniaJerarquia";

describe("InsigniaJerarquia", () => {
  it("muestra la insignia con el nivel y mención a MINCETUR", () => {
    render(<InsigniaJerarquia jerarquia={4} variante="insignia" contexto="lugar" />);
    expect(screen.getByRole("button").textContent).toContain("Jerarquía 4 · MINCETUR");
  });

  it("al hacer click abre el globo flotante mostrando solo la definición de Jerarquía 4", () => {
    render(<InsigniaJerarquia jerarquia={4} variante="sello" contexto="ruta" />);
    const boton = screen.getByRole("button");

    fireEvent.click(boton);

    const dialogo = screen.getByRole("dialog");
    expect(dialogo).toBeTruthy();
    expect(dialogo.textContent).toContain("Jerarquía 4 · MINCETUR");
    expect(dialogo.textContent).toContain("Internacional");
    expect(dialogo.textContent).toContain("Atractivo de clase mundial");
    expect(dialogo.textContent).toContain("Machupicchu");
    // Verifica que NO lista las otras jerarquías
    expect(dialogo.textContent).not.toContain("Jerarquía 3");
    expect(dialogo.textContent).not.toContain("Jerarquía 2");
    expect(dialogo.textContent).not.toContain("Jerarquía 1");
    expect(dialogo.textContent).toContain(
      "Esta ruta incluye al menos un atractivo con esta máxima distinción",
    );
  });

  it("muestra solo la definición de Jerarquía 3 cuando corresponde", () => {
    render(<InsigniaJerarquia jerarquia={3} variante="insignia" contexto="lugar" />);
    fireEvent.click(screen.getByRole("button"));

    const dialogo = screen.getByRole("dialog");
    expect(dialogo).toBeTruthy();
    expect(dialogo.textContent).toContain("Jerarquía 3 · MINCETUR");
    expect(dialogo.textContent).toContain("Nacional");
    expect(dialogo.textContent).toContain("Gran significación nacional");
    expect(dialogo.textContent).toContain("Kuélap");
    // Verifica que NO lista las otras jerarquías
    expect(dialogo.textContent).not.toContain("Jerarquía 4");
    expect(dialogo.textContent).not.toContain("Jerarquía 2");
    expect(dialogo.textContent).not.toContain("Jerarquía 1");
    expect(dialogo.textContent).toContain("Calificación oficial según el inventario turístico del MINCETUR");
  });

  it("permite cerrar el globo con el botón de cerrar", () => {
    render(<InsigniaJerarquia jerarquia={4} variante="insignia" />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("dialog")).toBeTruthy();

    const botonCerrar = screen.getByRole("button", { name: /Cerrar explicación/i });
    fireEvent.click(botonCerrar);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("permite cerrar el globo presionando Escape", () => {
    render(<InsigniaJerarquia jerarquia={4} variante="insignia" />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("dialog")).toBeTruthy();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
