import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { irA, OPCIONES, pedidosA, ponerApi, VERSION } from "../pruebas/api";
import { plano } from "../pruebas/texto";

vi.mock("../piezas/MapaRuta", () => ({ default: () => <div data-testid="mapa" /> }));

async function abrir(rutas: Parameters<typeof ponerApi>[0] = {}) {
  const api = ponerApi(rutas);
  render(<App />);
  await screen.findByRole("combobox", { name: "Punto de partida" });
  return api;
}

const generar = () => userEvent.click(screen.getByRole("button", { name: "Generar mis rutas" }));
const consultaPedida = (api: ReturnType<typeof ponerApi>) => pedidosA(api, "/v1/viajes").at(-1);

describe("el formulario", () => {
  it("se arma con lo que dice el API: orígenes, intereses y días", async () => {
    await abrir();
    const origen = screen.getByRole("combobox", { name: "Punto de partida" });
    expect(
      within(origen)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(OPCIONES.origenes.map((o) => o.nombre));
    expect(screen.getAllByRole("checkbox").map((c) => c.closest("label")?.textContent)).toEqual(
      OPCIONES.intereses.map((i) => i.etiqueta),
    );
    expect(screen.getAllByRole("radio")).toHaveLength(12);
    const dias = screen.getByRole("spinbutton", { name: "Días disponibles" });
    expect(dias).toHaveProperty("value", "6");
    expect(dias.getAttribute("max")).toBe(String(OPCIONES.dias.maximo));
  });

  it("propone el mes que viene, también en diciembre", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    await abrir();
    expect(screen.getByRole("radio", { name: "Noviembre" })).toHaveProperty("checked", true);
  });

  it("en diciembre propone enero", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 11, 15));
    await abrir();
    expect(screen.getByRole("radio", { name: "Enero" })).toHaveProperty("checked", true);
  });

  it("manda la consulta en la URL, que es el enlace del viaje", async () => {
    const api = await abrir();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Punto de partida" }), "cusco");
    await userEvent.click(screen.getByRole("button", { name: "Un día más" }));
    await userEvent.click(screen.getByRole("checkbox", { name: "Playa" }));
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    await generar();

    await screen.findByRole("heading", { level: 1, name: "Tres viajes para ti" });
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=cusco&mes=7&dias=7&intereses=playa");
    await waitFor(() =>
      expect(window.location.search).toBe(`?origen=cusco&mes=7&dias=7&intereses=playa&v=${VERSION}`),
    );
  });

  it("«Sorpréndeme» pide solo fuera del circuito; Enter en un campo, no", async () => {
    const api = await abrir();
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    await userEvent.click(screen.getByRole("button", { name: "Sorpréndeme" }));
    await screen.findByRole("heading", { level: 1, name: "Tres viajes para ti" });
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&sorpresa=true");

    await userEvent.click(screen.getByRole("link", { name: "Cambiar" }));
    await userEvent.type(await screen.findByRole("spinbutton", { name: "Días disponibles" }), "{Enter}");
    await screen.findByRole("heading", { level: 1, name: "Tres viajes para ti" });
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6");
  });

  it("el presupuesto y la altitud solo viajan si se bajan del extremo", async () => {
    const api = await abrir();
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    const presupuesto = screen.getByRole("slider", { name: /Presupuesto total/ });
    const altitud = screen.getByRole("slider", { name: /Altitud máxima/ });
    expect(presupuesto.getAttribute("aria-valuetext")).toBe("Sin tope");

    fireEvent.change(presupuesto, { target: { value: "1800" } });
    fireEvent.change(altitud, { target: { value: "2500" } });
    expect(plano(document.querySelector(`output[for="${presupuesto.id}"]`)?.textContent)).toBe("S/ 1 800");
    expect(plano(document.querySelector(`output[for="${altitud.id}"]`)?.textContent)).toBe("2 500 m");
    await generar();
    await screen.findByRole("heading", { level: 1, name: "Tres viajes para ti" });
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&presupuesto=1800&altitud_max=2500");

    await userEvent.click(screen.getByRole("link", { name: "Cambiar" }));
    const otraVez = await screen.findByRole("slider", { name: /Presupuesto total/ });
    expect(otraVez).toHaveProperty("value", "1800");
    fireEvent.change(otraVez, { target: { value: otraVez.getAttribute("max") } });
    expect(otraVez.getAttribute("aria-valuetext")).toBe("Sin tope");
    await generar();
    await waitFor(() =>
      expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&altitud_max=2500"),
    );
  });

  it("con fecha de salida manda la fecha, y el mes la sigue", async () => {
    const api = await abrir();
    const fecha = screen.getByLabelText(/Ya tienes fecha de salida/);
    fireEvent.change(fecha, { target: { value: "2027-07-20" } });
    expect(screen.getByRole("radio", { name: "Julio" })).toHaveProperty("checked", true);

    // Elegir otro mes suelta la fecha: no pueden contradecirse.
    await userEvent.click(screen.getByRole("radio", { name: "Agosto" }));
    expect(fecha).toHaveProperty("value", "");
    fireEvent.change(fecha, { target: { value: "2027-07-20" } });
    await generar();
    await screen.findByRole("heading", { level: 1, name: "Tres viajes para ti" });
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&fecha_inicio=2027-07-20&dias=6");
  });

  it("al editar, abre con la consulta que ya había", async () => {
    irA("/?origen=cusco&mes=7&dias=4&intereses=playa&presupuesto=1800#/editar");
    await abrir();
    expect(screen.getByRole("combobox", { name: "Punto de partida" })).toHaveProperty("value", "cusco");
    expect(screen.getByRole("spinbutton", { name: "Días disponibles" })).toHaveProperty("value", "4");
    expect(screen.getByRole("checkbox", { name: "Playa" })).toHaveProperty("checked", true);
    expect(screen.getByRole("checkbox", { name: "Naturaleza" })).toHaveProperty("checked", false);
    expect(screen.getByRole("radio", { name: "Julio" })).toHaveProperty("checked", true);
    expect(screen.getByRole("slider", { name: /Presupuesto total/ })).toHaveProperty("value", "1800");
  });

  it("si el servidor todavía no responde, lo dice y deja reintentar", async () => {
    let intentos = 0;
    const api = ponerApi({
      "/v1/opciones": () => {
        intentos += 1;
        return intentos === 1
          ? { estado: 503, cuerpo: { detail: "El motor todavía no tiene sus datos." } }
          : { cuerpo: OPCIONES };
      },
    });
    render(<App />);
    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("El servidor está arrancando");
    expect(alerta.textContent).toContain("El motor todavía no tiene sus datos.");

    await userEvent.click(within(alerta).getByRole("button", { name: "Volver a intentar" }));
    await screen.findByRole("combobox", { name: "Punto de partida" });
    expect(pedidosA(api, "/v1/opciones")).toHaveLength(2);
  });
});
