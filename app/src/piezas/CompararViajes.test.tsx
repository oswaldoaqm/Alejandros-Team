import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "../App";
import type { Ruta } from "../api/tipos";
import { horas, soles } from "../formato";
import { irA, ponerApi, RESPUESTA, viajesPara } from "../pruebas/api";
import { plano } from "../pruebas/texto";
import { CompararViajes } from "./CompararViajes";

describe("comparación de viajes", () => {
  it("muestra las cifras y los motivos de las tres rutas recibidas, sin tratar el puntaje como probabilidad", () => {
    render(<CompararViajes rutas={RESPUESTA.rutas} />);
    const opciones = within(
      screen.getByRole("list", { name: "Comparación de viajes propuestos" }),
    ).getAllByRole("listitem");
    expect(opciones).toHaveLength(3);

    RESPUESTA.rutas.forEach((ruta, indice) => {
      const texto = plano(opciones[indice]?.textContent);
      expect(texto).toContain(ruta.polo.nombre);
      expect(texto).toContain(`P50: ${plano(soles(ruta.costo.p50))}`);
      expect(texto).toContain(`P80: ${plano(soles(ruta.costo.p80))}`);
      expect(texto).toContain(plano(horas(ruta.traslado.horas ?? 0)));
      expect(texto).toContain(ruta.motivos[0]);
    });
    expect(plano(screen.getByText(/El puntaje interno solo ordena/).textContent)).toContain(
      "no es una probabilidad",
    );
  });

  it("actualiza la comparación si cambian los datos devueltos por el motor", () => {
    const { rerender } = render(<CompararViajes rutas={RESPUESTA.rutas.slice(0, 2)} />);
    const primera = RESPUESTA.rutas[0];
    if (!primera) throw new Error("Falta la primera ruta del ejemplo.");
    const nueva: Ruta = {
      ...primera,
      puntaje: 0.31,
      costo: { ...primera.costo, p50: 1200, p80: 1450 },
      traslado: { ...primera.traslado, horas: 5.5 },
    };
    rerender(<CompararViajes rutas={[nueva, ...RESPUESTA.rutas.slice(1, 2)]} />);
    const primeraOpcion = within(
      screen.getByRole("list", { name: "Comparación de viajes propuestos" }),
    ).getAllByRole("listitem")[0];
    const texto = plano(primeraOpcion?.textContent);
    expect(texto).toContain("0,31");
    expect(texto).toContain("P50: S/ 1 200");
    expect(texto).toContain("P80: S/ 1 450");
    expect(texto).toContain("5 h 30");
    expect(texto).not.toContain(`P50: ${plano(soles(primera.costo.p50))}`);
  });

  it("no ocupa espacio si solo hay una ruta", () => {
    const { container } = render(<CompararViajes rutas={RESPUESTA.rutas.slice(0, 1)} />);
    expect(container.childElementCount).toBe(0);
  });

  it("aparece en los resultados reales de la búsqueda, y se oculta cuando llega una sola ruta", async () => {
    irA("/?origen=lima&mes=7&dias=4");
    ponerApi();
    const { unmount } = render(<App />);
    expect(await screen.findByRole("heading", { name: "Compara antes de elegir" })).toBeDefined();
    unmount();

    irA("/?origen=lima&mes=7&dias=4");
    ponerApi({
      "/v1/viajes": (url: URL) => {
        const respuesta = viajesPara(url);
        return { cuerpo: { ...respuesta, rutas: respuesta.rutas.slice(0, 1) } };
      },
    });
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Un viaje para ti" })).toBeDefined();
    expect(screen.queryByRole("heading", { name: "Compara antes de elegir" })).toBeNull();
  });
});
