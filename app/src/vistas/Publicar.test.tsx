import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App";
import type { PropsDeMapaLugar } from "../piezas/MapaLugar";
import { eventosQuePublican, irA, type PedidoRecibido, PUBLICADO, pedidosA, ponerApi } from "../pruebas/api";
import { REGIONES } from "../regiones";
import { ultimoInicio } from "./Publicar";

// El mapa de verdad necesita WebGL. Aquí es un botón que marca Villa Rica, y dice adónde se
// acercaría y dónde quedó la marca.
vi.mock("../piezas/MapaLugar", () => ({
  default: ({ lugar, cerca, alElegir }: PropsDeMapaLugar) => (
    <div data-testid="mapa" data-cerca={cerca ? `${cerca.lat},${cerca.lon}` : ""}>
      <button type="button" onClick={() => alElegir({ lat: -10.7345, lon: -75.2712 })}>
        Marcar en el mapa
      </button>
      {lugar ? <span data-testid="marca">{`${lugar.lat},${lugar.lon}`}</span> : null}
    </div>
  ),
}));

const CLAVE = "clave-de-prueba-0123";
const ENTIDAD = "Municipalidad Distrital de Villa Rica";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 9, 2, 10));
});

async function abrir(rutas: Parameters<typeof ponerApi>[0] = {}) {
  irA("/#/publicar");
  const api = ponerApi(rutas);
  render(<App />);
  await screen.findByRole("heading", { level: 1, name: "Publicar un evento" });
  return api;
}

const casilla = (nombre: string | RegExp) => screen.getByLabelText(nombre) as HTMLInputElement;
const escribir = (nombre: string | RegExp, texto: string) =>
  fireEvent.change(casilla(nombre), { target: { value: texto } });

/** Llena lo obligatorio; `cambios` reemplaza o agrega casillas por su rótulo. */
function llenar(cambios: Record<string, string> = {}) {
  const valores: Record<string, string> = {
    "Nombre del evento": "Feria de Productores",
    Empieza: "2026-11-13",
    Región: "Pasco",
    Provincia: "Oxapampa",
    Distrito: "Villa Rica",
    "Entidad que publica": ENTIDAD,
    "Clave de publicador": CLAVE,
    ...cambios,
  };
  for (const [rotulo, valor] of Object.entries(valores)) escribir(rotulo, valor);
}

const publicar = () => userEvent.click(screen.getByRole("button", { name: "Publicar el evento" }));

describe("publicar un evento", () => {
  it("pide lo que pide el contrato, con las 25 regiones", async () => {
    await abrir();
    expect(document.title).toBe("Publicar un evento · DreemGO");
    const opciones = within(screen.getByRole("combobox", { name: "Región" })).getAllByRole("option");
    expect(opciones.map((o) => o.textContent)).toEqual(["Elige una", ...REGIONES.map((r) => r.nombre)]);
    expect(REGIONES).toHaveLength(25);
    for (const obligatoria of ["Nombre del evento", "Empieza", "Región", "Provincia", "Distrito"]) {
      expect(casilla(obligatoria).required, obligatoria).toBe(true);
    }
    expect(casilla(/^Termina/).required).toBe(false);
    expect(casilla("Clave de publicador").type).toBe("password");
    // Se publican los eventos de doce meses: el calendario no muestra más.
    expect(casilla("Empieza").max).toBe("2027-09-30");
  });

  it("manda el evento con la clave en su cabecera y muestra cómo lo verá el viajero", async () => {
    const recibidos: PedidoRecibido[] = [];
    const api = await abrir({ "/v1/eventos": eventosQuePublican(recibidos) });
    llenar({
      "Termina Si dura un día, se deja en blanco": "2026-11-15",
      "Tipo de evento Opcional": "Feria gastronómica",
      "Enlace con más información Opcional": "https://www.munivillarica.gob.pe/festival",
    });
    await userEvent.click(await screen.findByRole("button", { name: "Marcar en el mapa" }));
    expect(screen.getByText("Marcado en \u221210,73450, \u221275,27120.")).toBeDefined();
    await publicar();

    const titulo = await screen.findByRole("heading", { level: 1, name: "Evento publicado" });
    expect(document.activeElement).toBe(titulo);
    expect(recibidos).toHaveLength(1);
    expect(recibidos[0]?.cabeceras.get("X-Clave-Publicador")).toBe(CLAVE);
    expect(recibidos[0]?.cuerpo).toEqual({
      nombre: "Feria de Productores",
      tipo: "Feria gastronómica",
      fecha_inicio: "2026-11-13",
      fecha_fin: "2026-11-15",
      distrito: "Villa Rica",
      provincia: "Oxapampa",
      region: "Pasco",
      lat: -10.7345,
      lon: -75.2712,
      url: "https://www.munivillarica.gob.pe/festival",
      publicado_por: ENTIDAD,
    });
    expect(screen.getByText(/sale también en las rutas que duermen o paran a 10 km o menos/)).toBeDefined();
    expect(screen.getByText(new RegExp(`Publicado por ${ENTIDAD}`))).toBeDefined();
    expect(screen.getByRole("link", { name: /Feria de Productores/ }).getAttribute("href")).toBe(
      PUBLICADO.url,
    );
    // Las opciones se piden otra vez: traen la versión de datos, que cambió.
    await waitFor(() => expect(pedidosA(api, "/v1/opciones")).toHaveLength(2));
  });

  it("sin marcar el lugar ni la fecha de fin: un día, y solo en el calendario", async () => {
    const recibidos: PedidoRecibido[] = [];
    await abrir({ "/v1/eventos": eventosQuePublican(recibidos) });
    llenar();
    expect(screen.getByText("Todavía sin marcar.")).toBeDefined();
    await publicar();

    await screen.findByRole("heading", { level: 1, name: "Evento publicado" });
    expect(recibidos[0]?.cuerpo).toMatchObject({
      fecha_inicio: "2026-11-13",
      fecha_fin: "2026-11-13",
      lat: null,
      lon: null,
      tipo: null,
      url: null,
    });
    expect(screen.getByText(/Como no marcaste dónde es, no sale en ninguna ruta/)).toBeDefined();
  });

  it("al elegir la región, el mapa se acerca a su ciudad principal", async () => {
    await abrir();
    const mapa = await screen.findByTestId("mapa");
    expect(mapa.dataset.cerca).toBe("");
    escribir("Región", "Áncash");
    expect(mapa.dataset.cerca).toBe("-9.5278,-77.5278");
  });

  it("la marca se puede quitar", async () => {
    await abrir();
    await userEvent.click(await screen.findByRole("button", { name: "Marcar en el mapa" }));
    expect(screen.getByTestId("marca").textContent).toBe("-10.7345,-75.2712");
    await userEvent.click(screen.getByRole("button", { name: "Quitar la marca" }));
    expect(screen.queryByTestId("marca")).toBeNull();
    expect(screen.getByText("Todavía sin marcar.")).toBeDefined();
  });

  it("después de publicar, el calendario se pide otra vez y ya trae el evento", async () => {
    const recibidos: PedidoRecibido[] = [];
    const api = await abrir({ "/v1/eventos": eventosQuePublican(recibidos) });
    // Antes de publicar se miró el calendario de noviembre: esa respuesta ya no vale.
    await userEvent.click(screen.getByRole("link", { name: "Fiestas" }));
    await userEvent.click(await screen.findByRole("radio", { name: "Noviembre" }));
    await waitFor(() => expect(pedidosA(api, "/v1/eventos")).toHaveLength(2));
    window.location.hash = "#/publicar";
    await screen.findByRole("heading", { level: 1, name: "Publicar un evento" });

    llenar();
    await publicar();
    await userEvent.click(await screen.findByRole("link", { name: "Ver el calendario de noviembre" }));

    await screen.findByRole("heading", { level: 1, name: "Fiestas y eventos" });
    expect(window.location.hash).toBe("#/calendario/11");
    expect(screen.getByRole("radio", { name: "Noviembre" })).toHaveProperty("checked", true);
    const noviembre = "/v1/eventos?desde=2026-11-01&hasta=2026-11-30";
    await waitFor(() => expect(pedidosA(api, "/v1/eventos").filter((p) => p === noviembre)).toHaveLength(2));
  });

  it("«Publicar otro evento» no hace escribir de nuevo quién publica ni dónde", async () => {
    await abrir({ "/v1/eventos": eventosQuePublican([]) });
    llenar();
    await publicar();
    await userEvent.click(await screen.findByRole("button", { name: "Publicar otro evento" }));

    const titulo = await screen.findByRole("heading", { level: 1, name: "Publicar un evento" });
    expect(document.activeElement).toBe(titulo);
    expect(casilla("Nombre del evento").value).toBe("");
    expect(casilla("Empieza").value).toBe("");
    expect(casilla("Entidad que publica").value).toBe(ENTIDAD);
    expect(casilla("Clave de publicador").value).toBe(CLAVE);
    expect(casilla("Región").value).toBe("Pasco");
    expect(casilla("Distrito").value).toBe("Villa Rica");
  });
});

describe("cuando no se publica", () => {
  const noPublica = (estado: number, detail: unknown) => ({
    "/v1/eventos": eventosQuePublican([], { estado, cuerpo: { detail } }),
  });

  it("con la clave equivocada, lo dice arriba y en la casilla de la clave", async () => {
    await abrir(noPublica(401, "Falta la clave de publicador o no es la correcta."));
    llenar();
    await publicar();

    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("No se publicó");
    expect(alerta.textContent).toContain("Falta la clave de publicador o no es la correcta.");
    expect(document.activeElement).toBe(alerta);
    const clave = casilla("Clave de publicador");
    expect(clave.getAttribute("aria-invalid")).toBe("true");
    const descrita = (clave.getAttribute("aria-describedby") ?? "").split(" ");
    expect(descrita.map((id) => document.getElementById(id)?.textContent)).toEqual([
      "Falta la clave de publicador o no es la correcta.",
      "La que el equipo de DreemGO le dio a tu entidad. No se guarda en este navegador.",
    ]);
    // Lo escrito sigue ahí para corregir y volver a enviar.
    expect(casilla("Nombre del evento").value).toBe("Feria de Productores");
  });

  it("si el servidor no acepta publicaciones, no le echa la culpa a la clave", async () => {
    await abrir(noPublica(403, "Este servidor no acepta publicaciones."));
    llenar();
    await publicar();
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Este servidor no acepta publicaciones.",
    );
    expect(casilla("Clave de publicador").getAttribute("aria-invalid")).toBeNull();
  });

  it("cada error del contrato va a su casilla, y el que es de todo el evento, arriba", async () => {
    await abrir(
      noPublica(422, [
        { campo: "region", mensaje: "Región desconocida. Opciones: Amazonas, Áncash.", tipo: "value_error" },
        { campo: "lat", mensaje: "Debe ser menor o igual que 0.1.", tipo: "less_than_equal" },
        { campo: "evento", mensaje: "Un evento no puede durar más de 60 días.", tipo: "value_error" },
      ]),
    );
    llenar();
    await publicar();

    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("Un evento no puede durar más de 60 días.");
    expect(alerta.textContent).not.toContain("Región desconocida");
    const region = casilla("Región");
    expect(region.getAttribute("aria-invalid")).toBe("true");
    expect(document.getElementById(region.getAttribute("aria-describedby") ?? "")?.textContent).toBe(
      "Región desconocida. Opciones: Amazonas, Áncash.",
    );
    // Las coordenadas son una sola casilla: el lugar.
    expect(screen.getByText("Debe ser menor o igual que 0.1.")).toBeDefined();
    expect(casilla("Nombre del evento").getAttribute("aria-invalid")).toBeNull();
  });

  it("si solo hay errores de casillas, arriba dice dónde mirar", async () => {
    await abrir(
      noPublica(422, [{ campo: "fecha_fin", mensaje: "El evento ya terminó.", tipo: "value_error" }]),
    );
    llenar();
    await publicar();
    expect((await screen.findByRole("alert")).textContent).toContain("está marcado en su casilla");
    expect(casilla(/^Termina/).getAttribute("aria-invalid")).toBe("true");
  });

  it("si no se pudo guardar, muestra lo que dice el servidor", async () => {
    await abrir(noPublica(503, "No pudimos guardar el evento. Vuelve a intentarlo en un momento."));
    llenar();
    await publicar();
    expect((await screen.findByRole("alert")).textContent).toContain(
      "No pudimos guardar el evento. Vuelve a intentarlo en un momento.",
    );
    expect(screen.getByRole("button", { name: "Publicar el evento" })).toHaveProperty("disabled", false);
  });

  it("una clave con tildes o espacios ni se envía", async () => {
    const recibidos: PedidoRecibido[] = [];
    await abrir({ "/v1/eventos": eventosQuePublican(recibidos) });
    llenar({ "Clave de publicador": "clave con espacios y ñ" });
    await publicar();
    expect((await screen.findByRole("alert")).textContent).toContain("La clave no lleva espacios");
    expect(recibidos).toHaveLength(0);
    expect(casilla("Clave de publicador").getAttribute("aria-invalid")).toBe("true");
  });
});

describe("hasta cuándo se publica", () => {
  it("el mes en curso y los once que siguen", () => {
    expect(ultimoInicio(new Date(2026, 9, 2))).toBe("2027-09-30");
    expect(ultimoInicio(new Date(2026, 0, 31))).toBe("2026-12-31");
    expect(ultimoInicio(new Date(2027, 2, 15))).toBe("2028-02-29");
  });
});
