import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Costo } from "../api/tipos";
import { plano } from "../pruebas/texto";
import { BandaCosto, escalaDeBanda } from "./BandaCosto";

const COSTO: Costo = {
  moneda: "PEN",
  p20: 972,
  p50: 1157,
  p80: 1339,
  desglose: { transporte: 328, alojamiento: 415, alimentacion: 355, entradas: 59 },
  dentro_del_presupuesto: true,
  exceso: null,
  supuestos: ["Bus interprovincial de ida y vuelta: 604 km"],
};

describe("la escala de la banda", () => {
  it("ordena los tres percentiles dentro de la barra, con aire a los lados", () => {
    const { en, tope } = escalaDeBanda(COSTO, null);
    expect(tope).toBeNull();
    expect(en(COSTO.p20)).toBeGreaterThan(0);
    expect(en(COSTO.p20)).toBeLessThan(en(COSTO.p50));
    expect(en(COSTO.p50)).toBeLessThan(en(COSTO.p80));
    expect(en(COSTO.p80)).toBeLessThan(100);
  });

  it("dibuja el presupuesto si queda cerca, por debajo o por encima", () => {
    const debajo = escalaDeBanda(COSTO, 700);
    expect(debajo.tope).toBe(700);
    expect(debajo.en(700)).toBeLessThan(debajo.en(COSTO.p20));
    const encima = escalaDeBanda(COSTO, 1500);
    expect(encima.en(1500)).toBeGreaterThan(encima.en(COSTO.p80));
    expect(encima.en(1500)).toBeLessThan(100);
  });

  it("un presupuesto muy por encima no se dibuja: aplastaría la banda", () => {
    const { en, tope } = escalaDeBanda(COSTO, 5000);
    expect(tope).toBeNull();
    expect(en(COSTO.p80) - en(COSTO.p20)).toBeGreaterThan(50);
  });
});

describe("la banda de costo", () => {
  it("muestra el centro, la banda y en qué se va", () => {
    render(<BandaCosto costo={COSTO} presupuesto={null} />);
    expect(screen.getByText("S/ 1 157")).toBeDefined();
    expect(plano(screen.getByRole("img").getAttribute("aria-label"))).toBe(
      "Costo estimado por persona: entre S/ 972 y S/ 1 339, con centro en S/ 1 157.",
    );
    expect(screen.getAllByRole("listitem").map((li) => plano(li.textContent))).toEqual([
      "TransporteS/ 328",
      "AlojamientoS/ 415",
      "AlimentaciónS/ 355",
      "EntradasS/ 59",
      "Bus interprovincial de ida y vuelta: 604 km",
    ]);
  });

  it("dice si el costo central entra en el presupuesto o por cuánto lo pasa", () => {
    const { rerender, container } = render(<BandaCosto costo={COSTO} presupuesto={1500} />);
    expect(plano(container.textContent)).toContain("Tu presupuesto: S/ 1 500, y el costo central entra.");
    rerender(
      <BandaCosto costo={{ ...COSTO, dentro_del_presupuesto: false, exceso: 157 }} presupuesto={1000} />,
    );
    expect(plano(container.textContent)).toContain(
      "Tu presupuesto: S/ 1 000; el costo central lo pasa por S/ 157.",
    );
  });
});
