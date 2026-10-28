import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { coordenada, ElegirLugar, leerCoordenada } from "./ElegirLugar";
import type { Lugar, PropsDeMapaLugar } from "./MapaLugar";

vi.mock("./MapaLugar", () => ({
  default: ({ lugar, alElegir }: PropsDeMapaLugar) => (
    <div>
      <button type="button" onClick={() => alElegir({ lat: -9.52781, lon: -77.52779 })}>
        Marcar en el mapa
      </button>
      {lugar ? <span data-testid="marca">{`${lugar.lat},${lugar.lon}`}</span> : null}
    </div>
  ),
}));

const MENOS = "−";

/** La pieza con su estado, como la usa el formulario. `elegidos` anota cada lugar que se elige. */
function Prueba({ elegidos }: { elegidos: (Lugar | null)[] }) {
  const [lugar, poner] = useState<Lugar | null>(null);
  return (
    <ElegirLugar
      lugar={lugar}
      cerca={null}
      alElegir={(nuevo) => {
        elegidos.push(nuevo);
        poner(nuevo);
      }}
    />
  );
}

const casilla = (nombre: string) => screen.getByLabelText(nombre) as HTMLInputElement;
const escribir = (nombre: string, texto: string) =>
  fireEvent.change(casilla(nombre), { target: { value: texto } });

describe("las coordenadas, escritas", () => {
  it("se escriben con coma y con el signo menos de imprenta", () => {
    expect(coordenada(-9.5278)).toBe(`${MENOS}9,52780`);
    expect(coordenada(-0.03812)).toBe(`${MENOS}0,03812`);
    expect(coordenada(0.1)).toBe("0,10000");
  });

  it("se leen con coma o con punto, y con cualquiera de los dos signos", () => {
    expect(leerCoordenada("-9.5278")).toBe(-9.5278);
    expect(leerCoordenada(` ${MENOS}9,5278 `)).toBe(-9.5278);
    expect(leerCoordenada("-77")).toBe(-77);
    for (const malo of ["", "norte", "9,5,2", "-", "9°31'"]) expect(leerCoordenada(malo)).toBeNull();
  });
});

describe("elegir el lugar de un evento", () => {
  it("lo que se marca en el mapa se ve en la lectura y en las casillas", async () => {
    const elegidos: (Lugar | null)[] = [];
    render(<Prueba elegidos={elegidos} />);
    expect(screen.getByText("Todavía sin marcar.")).toBeDefined();
    await userEvent.click(await screen.findByRole("button", { name: "Marcar en el mapa" }));
    expect(screen.getByText(`Marcado en ${MENOS}9,52781, ${MENOS}77,52779.`)).toBeDefined();
    expect(casilla("Latitud").value).toBe(`${MENOS}9,52781`);
    expect(casilla("Longitud").value).toBe(`${MENOS}77,52779`);
  });

  it("escribir las dos coordenadas pone la marca, sin cambiarle el texto a quien escribe", async () => {
    const elegidos: (Lugar | null)[] = [];
    render(<Prueba elegidos={elegidos} />);
    escribir("Latitud", "-9.5");
    expect(elegidos).toEqual([]);
    expect(screen.getByText(/Hacen falta las dos/)).toBeDefined();
    escribir("Longitud", "-77,5");
    expect(elegidos).toEqual([{ lat: -9.5, lon: -77.5 }]);
    expect((await screen.findByTestId("marca")).textContent).toBe("-9.5,-77.5");
    expect(casilla("Latitud").value).toBe("-9.5");
    expect(casilla("Longitud").value).toBe("-77,5");
  });

  it("un punto fuera del Perú no se marca, y dice entre qué valores va", () => {
    const elegidos: (Lugar | null)[] = [];
    render(<Prueba elegidos={elegidos} />);
    escribir("Latitud", "40.4");
    escribir("Longitud", "-3.7");
    expect(elegidos).toEqual([]);
    expect(screen.getByText(/Ese punto queda fuera del Perú/).textContent).toContain(
      `de ${MENOS}18,40000 a 0,10000`,
    );
    expect(casilla("Latitud").getAttribute("aria-invalid")).toBe("true");
  });

  it("quitar la marca vacía las casillas", async () => {
    const elegidos: (Lugar | null)[] = [];
    render(<Prueba elegidos={elegidos} />);
    await userEvent.click(await screen.findByRole("button", { name: "Marcar en el mapa" }));
    await userEvent.click(screen.getByRole("button", { name: "Quitar la marca" }));
    expect(elegidos.at(-1)).toBeNull();
    expect(casilla("Latitud").value).toBe("");
    expect(screen.getByText("Todavía sin marcar.")).toBeDefined();
  });
});
