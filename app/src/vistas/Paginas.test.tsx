import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { EVENTOS, irA, POLO, PUBLICADO, pedidosA, ponerApi } from "../pruebas/api";
import { plano } from "../pruebas/texto";
import { nombreDelViaje } from "../textos";
import { ventanaDelMes } from "./PaginaCalendario";

vi.mock("../piezas/MapaRuta", () => ({ default: () => <div data-testid="mapa" /> }));

async function abrir(direccion: string, rutas: Parameters<typeof ponerApi>[0] = {}) {
  irA(direccion);
  const api = ponerApi(rutas);
  render(<App />);
  return api;
}

const ZONA = nombreDelViaje(POLO.polo.nombre).titulo;

describe("la zona de un viaje", () => {
  it("muestra dónde se duerme, los lugares, el clima mes a mes y las fiestas", async () => {
    await abrir(`/?mes=7#/polo/${POLO.polo.id}`);
    expect(await screen.findByRole("heading", { level: 1, name: ZONA })).toBeDefined();
    expect(plano(document.querySelector(".portada__datos")?.textContent)).toContain(
      `Duermes en ${POLO.polo.base.nombre}`,
    );
    expect(screen.getByRole("region", { name: "Qué hay para ver" })).toBeDefined();
    expect(screen.getByRole("region", { name: "El clima, mes a mes" })).toBeDefined();
    expect(screen.getByRole("region", { name: "Fiestas de los próximos meses" })).toBeDefined();
    // El clima abre en el mes de la consulta.
    expect(screen.getByRole("radio", { name: /^Julio/ })).toHaveProperty("checked", true);
    expect(screen.getByRole("link", { name: "Tus viajes" }).getAttribute("href")).toBe(
      "?origen=lima&mes=7&dias=6",
    );
    await waitFor(() => expect(document.title).toBe(`${ZONA} · DreemGO`));
  });

  it("lista primero los lugares más importantes, deja ver todos y abre cada uno en su hoja", async () => {
    await abrir(`/#/polo/${POLO.polo.id}`);
    const lugares = await screen.findByRole("region", { name: "Qué hay para ver" });
    const filas = () => within(lugares).getAllByRole("listitem");
    expect(POLO.recursos.length).toBeGreaterThan(8);
    expect(filas()).toHaveLength(8);
    await userEvent.click(
      within(lugares).getByRole("button", { name: `Ver los ${POLO.recursos.length} lugares` }),
    );
    expect(filas()).toHaveLength(POLO.recursos.length);
    expect(within(lugares).getByRole("button", { name: "Ver menos" }).getAttribute("aria-expanded")).toBe(
      "true",
    );

    const primero = POLO.recursos[0];
    if (!primero) throw new Error("La zona de prueba no trae lugares.");
    await userEvent.click(within(lugares).getByRole("button", { name: new RegExp(`^${primero.nombre}`) }));
    const hoja = screen.getByRole("dialog", { name: primero.nombre });
    expect(
      within(hoja)
        .getByRole("link", { name: /^Ver la ficha oficial/ })
        .getAttribute("href"),
    ).toBe(primero.url_ficha);
  });

  it("si la zona no existe, lo dice", async () => {
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
      screen.getByText(new RegExp(`^${deLaRegion}.eventos? en ${elegida}, en enero de 2027$`)),
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

  it("«#/calendario/11» abre en noviembre, y si el enlace pide otro mes, cambia", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    const api = await abrir("/?origen=cusco&mes=7&dias=4#/calendario/11");
    await screen.findByText(/eventos en noviembre de 2026$/);
    expect(screen.getByRole("radio", { name: "Noviembre" })).toHaveProperty("checked", true);
    expect(pedidosA(api, "/v1/eventos")).toEqual(["/v1/eventos?desde=2026-11-01&hasta=2026-11-30"]);

    window.location.hash = "#/calendario/12";
    await screen.findByText(/eventos en diciembre de 2026$/);
    expect(screen.getByRole("radio", { name: "Diciembre" })).toHaveProperty("checked", true);
  });

  it("un evento publicado dice quién lo publicó, y enlaza a donde dijo esa entidad", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    await abrir("/#/calendario/11", {
      "/v1/eventos": { cuerpo: { ...EVENTOS, eventos: [...EVENTOS.eventos, PUBLICADO] } },
    });
    const enlace = await screen.findByRole("link", { name: /Feria de Productores/ });
    expect(enlace.getAttribute("href")).toBe(PUBLICADO.url);
    const evento = enlace.closest("li") as HTMLElement;
    expect(plano(evento.textContent)).toContain("del 13 al 15 de noviembre");
    expect(evento.textContent).toContain("Villa Rica, Oxapampa, Pasco");
    expect(evento.textContent).toContain("Publicado por Municipalidad Distrital de Villa Rica");
    // La fecha la dio quien lo organiza: no lleva la nota de «aproximada».
    expect(evento.textContent).not.toContain("aproximada");
    // Y entra al filtro por región como cualquier otro.
    const regiones = within(screen.getByRole("combobox", { name: "Región" })).getAllByRole("option");
    expect(regiones.map((o) => o.textContent)).toContain("Pasco");
  });

  it("lo que empezó el mes anterior va aparte, después de lo que empieza en el mes", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    const viene = {
      ...PUBLICADO,
      id: "p-viene",
      nombre: "Feria que viene de octubre",
      fecha_inicio: "2026-10-28",
    };
    await abrir("/#/calendario/11", {
      "/v1/eventos": { cuerpo: { ...EVENTOS, eventos: [viene, PUBLICADO] } },
    });
    const aparte = await screen.findByRole("region", { name: "Empezaron en octubre y siguen en noviembre" });
    expect(within(aparte).getByRole("link", { name: /Feria que viene de octubre/ })).toBeDefined();
    const [primeraLista] = screen.getAllByRole("list");
    expect(
      within(primeraLista as HTMLElement).getByRole("link", { name: /Feria de Productores/ }),
    ).toBeDefined();
    expect(screen.getByText(/^2.eventos en noviembre de 2026$/)).toBeDefined();
  });

  it("invita a publicar a quien organiza un evento", async () => {
    await abrir("/#/calendario");
    await userEvent.click(await screen.findByRole("link", { name: "Publícala aquí" }));
    expect(window.location.hash).toBe("#/publicar");
  });
});

describe("moverse por la app", () => {
  it("el pie lleva a publicar un evento", async () => {
    await abrir("/");
    await screen.findByRole("button", { name: /^Desde/ });
    await userEvent.click(screen.getByRole("link", { name: "Publica un evento" }));
    const titulo = await screen.findByRole("heading", { level: 1, name: "Publicar un evento" });
    expect(document.activeElement).toBe(titulo);
    expect(window.location.hash).toBe("#/publicar");
  });

  it("cada pantalla pone su título y recibe el foco, para que se note el cambio", async () => {
    await abrir("/");
    await screen.findByRole("button", { name: /^Desde/ });
    expect(document.title).toBe("DreemGO · Tres viajes por el Perú, día por día");

    // Las secciones están dos veces: en la cabecera y, para el celular, en la barra de abajo.
    const primero = (nombre: string) => screen.getAllByRole("link", { name: nombre })[0] as HTMLElement;
    await userEvent.click(primero("Guardados"));
    const titulo = screen.getByRole("heading", { level: 1, name: "Guardados" });
    expect(document.activeElement).toBe(titulo);
    expect(document.title).toBe("Guardados · DreemGO");
    for (const enlace of screen.getAllByRole("link", { name: "Guardados" }))
      expect(enlace.getAttribute("aria-current")).toBe("page");

    await userEvent.click(primero("Cómo funciona"));
    expect(document.activeElement).toBe(screen.getByRole("heading", { level: 1, name: "Cómo funciona" }));
    expect(window.location.hash).toBe("#/acerca");

    // Atrás y adelante del navegador también cambian de pantalla.
    window.history.back();
    expect(await screen.findByRole("heading", { level: 1, name: "Guardados" })).toBeDefined();
  });

  it("«Saltar al contenido» lleva el foco al contenido sin cambiar de pantalla", async () => {
    await abrir("/#/acerca");
    await userEvent.click(screen.getByRole("button", { name: "Saltar al contenido" }));
    expect(document.activeElement).toBe(screen.getByRole("main"));
    expect(window.location.hash).toBe("#/acerca");
  });

  it("«Tus viajes», desde la zona, retrocede: el viaje abierto sigue abierto", async () => {
    const api = await abrir("/?origen=lima&mes=7&dias=4#/ruta/2");
    const aLaZona = await screen.findByRole("link", { name: /^Ver todos los lugares de la zona/ });
    const id = aLaZona.getAttribute("href")?.split("/").at(-1);
    api.mockClear();
    ponerApi({ [`/v1/polos/${id}`]: { cuerpo: POLO } });
    await userEvent.click(aLaZona);
    await screen.findByRole("heading", { level: 1, name: ZONA });

    await userEvent.click(screen.getByRole("link", { name: "Tus viajes" }));
    await screen.findByRole("link", { name: /^Ver todos los lugares de la zona/ });
    expect(window.location.hash).toBe("#/ruta/2");
  });
});
