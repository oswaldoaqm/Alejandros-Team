import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { EVENTOS, irA, POLO, pedidosA, ponerApi } from "../pruebas/api";
import { plano } from "../pruebas/texto";
import { ventanaDelMes } from "./PaginaCalendario";

vi.mock("../piezas/MapaRuta", () => ({ default: () => <div data-testid="mapa" /> }));

async function abrir(direccion: string, rutas: Parameters<typeof ponerApi>[0] = {}) {
  irA(direccion);
  const api = ponerApi(rutas);
  render(<App />);
  return api;
}

describe("la ficha de un polo", () => {
  it("muestra dónde se duerme, el clima mes a mes, los lugares y las fiestas", async () => {
    await abrir(`/?mes=7#/polo/${POLO.polo.id}`);
    expect(await screen.findByRole("heading", { level: 1, name: POLO.polo.nombre })).toBeDefined();
    expect(plano(document.querySelector(".bajada")?.textContent)).toContain(
      `se duerme en ${POLO.polo.base.nombre}`,
    );
    // El clima abre en el mes de la consulta.
    expect(screen.getByRole("radio", { name: /^Julio/ })).toHaveProperty("checked", true);
    expect(screen.getByRole("link", { name: "Volver a tus rutas" }).getAttribute("href")).toBe(
      "?origen=lima&mes=7&dias=6",
    );
    await waitFor(() => expect(document.title).toBe(`${POLO.polo.nombre} · DreemGO`));
  });

  it("lista primero los diez lugares de mayor jerarquía y deja ver todos", async () => {
    await abrir(`/#/polo/${POLO.polo.id}`);
    await screen.findByRole("heading", { level: 1, name: POLO.polo.nombre });
    const fichas = () => screen.getAllByRole("link", { name: /Ficha oficial/ });
    expect(POLO.recursos.length).toBeGreaterThan(10);
    expect(fichas()).toHaveLength(10);
    await userEvent.click(screen.getByRole("button", { name: `Ver las ${POLO.recursos.length}` }));
    expect(fichas()).toHaveLength(POLO.recursos.length);
    expect(
      screen.getByRole("button", { name: "Ver solo las 10 primeras" }).getAttribute("aria-expanded"),
    ).toBe("true");
  });

  it("si el polo no existe, lo dice", async () => {
    await abrir("/#/polo/9999");
    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("No lo encontramos");
  });
});

describe("el calendario de fiestas", () => {
  it("la ventana de un mes es su próxima vez, con su último día", () => {
    const hoy = new Date(2026, 9, 1);
    expect(ventanaDelMes(10, hoy)).toEqual({ desde: "2026-10-01", hasta: "2026-10-31", anio: 2026 });
    expect(ventanaDelMes(1, hoy)).toEqual({ desde: "2027-01-01", hasta: "2027-01-31", anio: 2027 });
    expect(ventanaDelMes(2, new Date(2028, 0, 15))).toEqual({
      desde: "2028-02-01",
      hasta: "2028-02-29",
      anio: 2028,
    });
  });

  it("pide los eventos del mes y deja cambiar de mes y de región", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    const api = await abrir("/#/calendario");
    await screen.findByText(new RegExp(`^${EVENTOS.eventos.length}.eventos en octubre de 2026$`));
    expect(pedidosA(api, "/v1/eventos")).toEqual(["/v1/eventos?desde=2026-10-01&hasta=2026-10-31"]);
    expect(
      screen.getAllByRole("link", { name: /./ }).filter((a) => a.getAttribute("target") === "_blank"),
    ).toHaveLength(EVENTOS.eventos.filter((e) => e.url).length);

    await userEvent.click(screen.getByRole("radio", { name: "Enero" }));
    await waitFor(() =>
      expect(pedidosA(api, "/v1/eventos").at(-1)).toBe("/v1/eventos?desde=2027-01-01&hasta=2027-01-31"),
    );

    const regiones = [...new Set(EVENTOS.eventos.map((e) => e.region))].sort((a, b) =>
      a.localeCompare(b, "es"),
    );
    const region = screen.getByRole("combobox", { name: "Región" });
    expect(
      within(region)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Todo el país", ...regiones]);
    const elegida = regiones[0] as string;
    await userEvent.selectOptions(region, elegida);
    const deLaRegion = EVENTOS.eventos.filter((e) => e.region === elegida).length;
    expect(
      screen.getByText(new RegExp(`^${deLaRegion}.eventos? en enero de 2027 · ${elegida}$`)),
    ).toBeDefined();
  });

  it("con una consulta abierta, abre en su mes y ofrece armar el viaje", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    const api = await abrir("/?origen=cusco&mes=7&dias=4#/calendario");
    await screen.findByText(/eventos en julio de 2027$/);
    expect(pedidosA(api, "/v1/eventos")).toEqual(["/v1/eventos?desde=2027-07-01&hasta=2027-07-31"]);
    expect(screen.getByRole("link", { name: "Armar un viaje para julio" }).getAttribute("href")).toBe(
      "?origen=cusco&mes=7&dias=4#/editar",
    );
  });
});

describe("moverse por la app", () => {
  it("cada pantalla pone su título y recibe el foco, para que se note el cambio", async () => {
    await abrir("/");
    await screen.findByRole("combobox", { name: "Punto de partida" });
    expect(document.title).toBe("DreemGO · Tres viajes por el Perú, día por día");

    await userEvent.click(screen.getByRole("link", { name: "Mis viajes" }));
    const titulo = screen.getByRole("heading", { level: 1, name: "Mis viajes" });
    expect(document.activeElement).toBe(titulo);
    expect(document.title).toBe("Mis viajes · DreemGO");
    expect(screen.getByRole("link", { name: "Mis viajes" }).getAttribute("aria-current")).toBe("page");

    await userEvent.click(screen.getByRole("link", { name: "Fuentes y cómo funciona" }));
    expect(document.activeElement).toBe(screen.getByRole("heading", { level: 1, name: "Cómo funciona" }));
    expect(window.location.hash).toBe("#/acerca");

    // Atrás y adelante del navegador también cambian de pantalla.
    window.history.back();
    expect(await screen.findByRole("heading", { level: 1, name: "Mis viajes" })).toBeDefined();
  });

  it("«Saltar al contenido» lleva el foco al contenido sin cambiar de pantalla", async () => {
    await abrir("/#/acerca");
    await userEvent.click(screen.getByRole("button", { name: "Saltar al contenido" }));
    expect(document.activeElement).toBe(screen.getByRole("main"));
    expect(window.location.hash).toBe("#/acerca");
  });

  it("«Volver a tus rutas» retrocede: la ruta abierta sigue abierta", async () => {
    const api = await abrir("/?origen=lima&mes=7&dias=4#/ruta/2");
    const lista = within(await screen.findByRole("list", { name: "Rutas propuestas" })).getAllByRole("link");
    expect(lista[1]?.getAttribute("aria-current")).toBe("true");
    const alPolo = screen.getByRole("link", { name: /Ver todo lo que hay en el polo/ });
    const id = alPolo.getAttribute("href")?.split("/").at(-1);
    api.mockClear();
    ponerApi({ [`/v1/polos/${id}`]: { cuerpo: POLO } });
    await userEvent.click(alPolo);
    await screen.findByRole("heading", { level: 1, name: POLO.polo.nombre });

    await userEvent.click(screen.getByRole("link", { name: "Volver a tus rutas" }));
    await screen.findByRole("list", { name: "Rutas propuestas" });
    expect(window.location.hash).toBe("#/ruta/2");
  });
});
