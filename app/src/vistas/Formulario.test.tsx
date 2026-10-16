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
  await screen.findByRole("button", { name: /^Desde/ });
  return api;
}

/** Lo que dice una fila del formulario: «Desde Lima», «Cuándo Julio»… */
const fila = (nombre: RegExp) => plano(screen.getByRole("button", { name: nombre }).textContent);
const abrirFila = (nombre: RegExp) => userEvent.click(screen.getByRole("button", { name: nombre }));
const listo = () => userEvent.click(screen.getByRole("button", { name: "Listo" }));
const buscar = () => userEvent.click(screen.getByRole("button", { name: "Ver mis viajes" }));
const consultaPedida = (api: ReturnType<typeof ponerApi>) => pedidosA(api, "/v1/viajes").at(-1);
const enResultados = () => screen.findByRole("heading", { level: 1, name: "Tres viajes para ti" });

describe("el formulario", () => {
  it("se arma con lo que dice el API: orígenes, intereses y días", async () => {
    await abrir();
    expect(fila(/^Desde/)).toBe("Desde Lima");
    expect(plano(screen.getByRole("group", { name: "Días, con la ida y la vuelta" }).textContent)).toContain(
      "6 días",
    );

    await abrirFila(/^Desde/);
    const origenes = within(screen.getByRole("dialog", { name: "¿Desde dónde sales?" })).getAllByRole(
      "button",
      {
        pressed: false,
      },
    );
    expect(origenes.map((o) => o.textContent)).toEqual(OPCIONES.origenes.slice(1).map((o) => o.nombre));
    expect(screen.getByRole("button", { pressed: true }).textContent).toBe("Lima");
    await userEvent.click(screen.getByRole("button", { name: "Cerrar" }));

    await abrirFila(/^Qué te gusta/);
    expect(screen.getAllByRole("checkbox").map((c) => c.closest("label")?.textContent)).toEqual(
      OPCIONES.intereses.map((i) => i.etiqueta),
    );
  });

  it("propone el mes que viene, también en diciembre", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 1));
    await abrir();
    expect(fila(/^Cuándo/)).toBe("Cuándo Noviembre");
  });

  it("en diciembre propone enero", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 11, 15));
    await abrir();
    expect(fila(/^Cuándo/)).toBe("Cuándo Enero");
  });

  it("los días no pasan de lo que permite el API", async () => {
    await abrir();
    for (let i = 6; i < OPCIONES.dias.maximo; i++)
      await userEvent.click(screen.getByRole("button", { name: "Un día más" }));
    expect(screen.getByRole("button", { name: "Un día más" })).toHaveProperty("disabled", true);
    expect(plano(screen.getByRole("group", { name: /Días/ }).textContent)).toContain(
      `${OPCIONES.dias.maximo} días`,
    );
  });

  it("manda la consulta en la URL, que es el enlace del viaje", async () => {
    const api = await abrir();
    await abrirFila(/^Desde/);
    await userEvent.click(screen.getByRole("button", { name: "Cusco" }));
    expect(fila(/^Desde/)).toBe("Desde Cusco");
    await userEvent.click(screen.getByRole("button", { name: "Un día más" }));
    await abrirFila(/^Qué te gusta/);
    await userEvent.click(screen.getByRole("checkbox", { name: "Playa" }));
    await listo();
    expect(fila(/^Qué te gusta/)).toBe("Qué te gusta Playa");
    await abrirFila(/^Cuándo/);
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    await listo();
    await buscar();

    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=cusco&mes=7&dias=7&intereses=playa");
    await waitFor(() =>
      expect(window.location.search).toBe(`?origen=cusco&mes=7&dias=7&intereses=playa&v=${VERSION}`),
    );
  });

  it("la ciudad se busca sin tildes, y Enter elige la primera que coincide sin buscar el viaje", async () => {
    const api = await abrir();
    await abrirFila(/^Desde/);
    const buscador = screen.getByRole("searchbox", { name: "Buscar una ciudad" });
    await userEvent.type(buscador, "maldo");
    const hoja = screen.getByRole("dialog");
    expect(within(hoja).getAllByRole("button", { name: /Maldonado/ })).toHaveLength(1);
    await userEvent.type(buscador, "{Enter}");
    expect(fila(/^Desde/)).toBe("Desde Puerto Maldonado");
    expect(pedidosA(api, "/v1/viajes")).toHaveLength(0);
  });

  it("«Sorpréndeme» pide solo viajes fuera de Lima y Cusco; «Ver mis viajes», no", async () => {
    const api = await abrir();
    await abrirFila(/^Cuándo/);
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    await listo();
    await userEvent.click(screen.getByRole("button", { name: "Sorpréndeme fuera de Lima y Cusco" }));
    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&sorpresa=true");

    await userEvent.click(screen.getByRole("link", { name: "Cambiar" }));
    await screen.findByRole("heading", { level: 1, name: "Cambia tu viaje" });
    await buscar();
    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6");
  });

  it("«A dónde» propone tres viajes; sin nada escrito, sugiere zonas de imperdibles fuera de tu ciudad", async () => {
    await abrir();
    expect(fila(/^A dónde/)).toBe("A dónde Te proponemos tres");
    await abrirFila(/^A dónde/);
    const hoja = screen.getByRole("dialog", { name: "¿A dónde quieres ir?" });
    expect(within(hoja).getByRole("button", { pressed: true }).textContent).toBe(
      "Te proponemos tresLas zonas que mejor te quedan",
    );
    const zonas = await within(hoja).findAllByRole("button", { pressed: false });
    // Desde Lima, Miraflores no: es la misma ciudad.
    expect(zonas.map((z) => z.querySelector("span span")?.textContent)).toEqual([
      "Cuzco",
      "Trujillo",
      "Nasca",
      "Machupicchu Pueblo",
      "Yanque",
    ]);
    expect(plano(zonas[0]?.textContent)).toBe("CuzcoCentro Histórico del Cusco");
  });

  it("con un destino, el viaje es a esa zona y se abre directo; no hay «Sorpréndeme»", async () => {
    const api = await abrir();
    await abrirFila(/^A dónde/);
    const buscador = screen.getByRole("searchbox", { name: "Buscar una zona o un lugar" });
    await userEvent.type(buscador, "ocopa");
    const hoja = screen.getByRole("dialog");
    const [huancayo] = within(hoja).getAllByRole("button", { pressed: false });
    expect(plano(huancayo?.textContent)).toBe("HuancayoPor Convento de Santa Rosa de Ocopa");
    await userEvent.click(huancayo as HTMLElement);

    expect(fila(/^A dónde/)).toBe("A dónde Huancayo");
    expect(screen.queryByRole("button", { name: /Sorpréndeme/ })).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Ver mi viaje" }));
    await screen.findByRole("heading", { level: 1, name: "Huancayo" });
    expect(consultaPedida(api)).toMatch(/^\/v1\/viajes\?origen=lima&destino=33&mes=\d+&dias=6$/);
    expect(window.location.hash).toBe("#/ruta/1");
  });

  it("Enter elige la primera zona que coincide, y «Te proponemos tres» quita el destino", async () => {
    await abrir();
    await abrirFila(/^A dónde/);
    await userEvent.type(
      screen.getByRole("searchbox", { name: "Buscar una zona o un lugar" }),
      "colca{Enter}",
    );
    expect(fila(/^A dónde/)).toBe("A dónde Yanque");

    await abrirFila(/^A dónde/);
    expect(within(screen.getByRole("dialog")).getByRole("button", { pressed: true }).textContent).toContain(
      "Yanque",
    );
    await userEvent.click(screen.getByRole("button", { name: /^Te proponemos tres/ }));
    expect(fila(/^A dónde/)).toBe("A dónde Te proponemos tres");
    expect(screen.getByRole("button", { name: "Sorpréndeme fuera de Lima y Cusco" })).toBeTruthy();
  });

  it("al cambiar un viaje con destino, la fila nombra la zona", async () => {
    irA("/?origen=lima&destino=36&mes=7&dias=4#/editar");
    await abrir();
    await waitFor(() => expect(fila(/^A dónde/)).toBe("A dónde Cuzco"));
    expect(screen.getByRole("button", { name: "Ver mi viaje" })).toBeTruthy();
  });

  it("el presupuesto y la altura solo viajan si se bajan del extremo", async () => {
    const api = await abrir();
    await abrirFila(/^Cuándo/);
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    await listo();
    expect(fila(/^Presupuesto y altura/)).toBe("Presupuesto y altura Sin límites");

    await abrirFila(/^Presupuesto y altura/);
    const presupuesto = screen.getByRole("slider", { name: "Presupuesto por persona" });
    const altura = screen.getByRole("slider", { name: "Altura máxima" });
    expect(presupuesto.getAttribute("aria-valuetext")).toBe("Sin tope");
    expect(altura.getAttribute("aria-valuetext")).toBe("Sin límite");
    fireEvent.change(presupuesto, { target: { value: "1800" } });
    fireEvent.change(altura, { target: { value: "2500" } });
    expect(plano(document.querySelector(`output[for="${presupuesto.id}"]`)?.textContent)).toBe("S/ 1 800");
    expect(plano(document.querySelector(`output[for="${altura.id}"]`)?.textContent)).toBe("2 500 m");
    await listo();
    expect(fila(/^Presupuesto y altura/)).toBe(
      "Presupuesto y altura Hasta S/ 1 800, hasta 2 500 m de altura",
    );
    await buscar();
    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&presupuesto=1800&altitud_max=2500");

    await userEvent.click(screen.getByRole("link", { name: "Cambiar" }));
    await abrirFila(/^Presupuesto y altura/);
    const otraVez = screen.getByRole("slider", { name: "Presupuesto por persona" });
    expect(otraVez).toHaveProperty("value", "1800");
    fireEvent.change(otraVez, { target: { value: otraVez.getAttribute("max") } });
    expect(otraVez.getAttribute("aria-valuetext")).toBe("Sin tope");
    await listo();
    await buscar();
    await waitFor(() =>
      expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&altitud_max=2500"),
    );
  });

  it("vuela a lo lejano; con el interruptor apagado pide solo por tierra", async () => {
    const api = await abrir();
    const vuelos = screen.getByRole("switch", { name: "Vuelos" });
    expect(vuelos).toHaveProperty("checked", true);
    expect(plano(vuelos.closest("label")?.textContent)).toBe("Vuelos Si por tierra pasa de 16 h");
    await abrirFila(/^Cuándo/);
    await userEvent.click(screen.getByRole("radio", { name: "Julio" }));
    await listo();
    await buscar();
    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6");

    await userEvent.click(screen.getByRole("link", { name: "Cambiar" }));
    await screen.findByRole("heading", { level: 1, name: "Cambia tu viaje" });
    await userEvent.click(screen.getByRole("switch", { name: "Vuelos" }));
    expect(screen.getByRole("switch", { name: "Vuelos" })).toHaveProperty("checked", false);
    expect(plano(screen.getByRole("switch", { name: "Vuelos" }).closest("label")?.textContent)).toBe(
      "Vuelos Solo por tierra",
    );
    await buscar();
    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&mes=7&dias=6&solo_por_tierra=true");
  });

  it("con fecha de salida manda la fecha, y el mes la sigue", async () => {
    const api = await abrir();
    await abrirFila(/^Cuándo/);
    const fecha = screen.getByLabelText(/Ya tienes fecha de salida/);
    fireEvent.change(fecha, { target: { value: "2027-07-20" } });
    expect(screen.getByRole("radio", { name: "Julio" })).toHaveProperty("checked", true);

    // Elegir otro mes suelta la fecha: no pueden contradecirse.
    await userEvent.click(screen.getByRole("radio", { name: "Agosto" }));
    expect(fecha).toHaveProperty("value", "");
    fireEvent.change(fecha, { target: { value: "2027-07-20" } });
    await listo();
    expect(fila(/^Cuándo/)).toBe("Cuándo Sale el 20 de julio");
    await buscar();
    await enResultados();
    expect(consultaPedida(api)).toBe("/v1/viajes?origen=lima&fecha_inicio=2027-07-20&dias=6");
  });

  it("al cambiar el viaje, abre con la consulta que ya había", async () => {
    irA("/?origen=cusco&mes=7&dias=4&intereses=playa&presupuesto=1800&solo_por_tierra=true#/editar");
    await abrir();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Cambia tu viaje");
    expect(fila(/^Desde/)).toBe("Desde Cusco");
    expect(fila(/^Cuándo/)).toBe("Cuándo Julio");
    expect(plano(screen.getByRole("group", { name: /Días/ }).textContent)).toContain("4 días");
    expect(fila(/^Qué te gusta/)).toBe("Qué te gusta Playa");
    expect(fila(/^Presupuesto y altura/)).toBe("Presupuesto y altura Hasta S/ 1 800");
    expect(screen.getByRole("switch", { name: "Vuelos" })).toHaveProperty("checked", false);
  });

  it("si la lista de zonas no llega, el formulario sigue y la hoja lo dice", async () => {
    irA("/?origen=lima&destino=36&mes=7&dias=4#/editar");
    await abrir({ "/destinos.json": { estado: 404, cuerpo: {} } });
    await waitFor(() => expect(fila(/^A dónde/)).toBe("A dónde La zona elegida"));
    await abrirFila(/^A dónde/);
    expect((await within(screen.getByRole("dialog")).findByRole("status")).textContent).toBe(
      "No pudimos cargar las zonas. Revisa tu conexión y vuelve a abrir esta hoja.",
    );
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
    await screen.findByRole("button", { name: /^Desde/ });
    expect(pedidosA(api, "/v1/opciones")).toHaveLength(2);
  });
});
