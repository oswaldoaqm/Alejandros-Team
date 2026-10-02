import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { leerViajes } from "../almacen";
import type { PropsDeMapa } from "../piezas/MapaRuta";
import { irA, pedidosA, ponerApi, RESPUESTA, VERSION, viajesPara } from "../pruebas/api";
import { plano } from "../pruebas/texto";

// El mapa de verdad necesita WebGL, que aquí no hay: en su lugar va un bloque que dice qué recibió.
vi.mock("../piezas/MapaRuta", () => ({
  default: ({ puntos, dia, base }: PropsDeMapa) => (
    <div
      data-testid="mapa"
      data-puntos={puntos.length}
      data-dia={String(dia)}
      data-base={base?.nombre ?? ""}
    />
  ),
}));

const CONSULTA =
  "origen=lima&mes=7&dias=4&intereses=historia&intereses=naturaleza&presupuesto=700&altitud_max=3500";
const [A, B] = RESPUESTA.rutas;
if (!A || !B) throw new Error("El ejemplo del contrato trae menos de dos rutas.");

/** Para buscar por nombre accesible sin tropezar con los espacios que no parten la línea. */
const conNombre = (texto: string) => (nombre: string) => plano(nombre) === texto;

async function abrir(direccion = `/?${CONSULTA}`, rutas: Parameters<typeof ponerApi>[0] = {}) {
  irA(direccion);
  const api = ponerApi(rutas);
  render(<App />);
  return api;
}

async function tarjetas() {
  return within(await screen.findByRole("list", { name: "Rutas propuestas" })).getAllByRole("link");
}

const tituloDelDetalle = () =>
  plano(screen.getByRole("heading", { level: 2, name: /^Ruta [ABC]/ }).textContent);

describe("los resultados", () => {
  it("muestra las rutas para comparar y abre la primera", async () => {
    await abrir();
    const lista = await tarjetas();
    expect(lista).toHaveLength(RESPUESTA.rutas.length);
    RESPUESTA.rutas.forEach((ruta, i) => {
      const texto = plano(lista[i]?.textContent);
      expect(texto).toContain(ruta.polo.nombre);
      expect(texto).toContain(`${ruta.indicadores.paradas} paradas`);
      expect(texto).toContain("4 días");
    });
    expect(lista[0]?.getAttribute("aria-current")).toBe("true");
    expect(lista[1]?.getAttribute("aria-current")).toBeNull();
    expect(tituloDelDetalle()).toBe(`Ruta A${A.polo.nombre}`);
    expect(
      screen.getByText("Tres rutas desde Lima para julio, de la más a la menos recomendada."),
    ).toBeDefined();
  });

  it("el detalle trae motivos, avisos, itinerario con fichas, costo, mes y fuentes", async () => {
    await abrir();
    await tarjetas();
    for (const motivo of A.motivos) expect(screen.getByText(motivo)).toBeDefined();
    for (const aviso of A.avisos ?? []) expect(screen.getByText(plano(aviso.mensaje))).toBeDefined();
    expect(screen.getAllByRole("link", { name: /Ficha oficial/ })).toHaveLength(A.indicadores.paradas);
    expect(screen.getAllByRole("heading", { level: 4 })).toHaveLength(A.dias.length);
    expect(screen.getByText(A.estacionalidad.explicacion)).toBeDefined();
    for (const linea of RESPUESTA.atribucion) expect(screen.getByText(linea)).toBeDefined();
    const mapa = await screen.findByTestId("mapa");
    expect(mapa.dataset.puntos).toBe(String(A.indicadores.paradas));
    expect(mapa.dataset.base).toBe(A.polo.base.nombre);
  });

  it("al elegir otra tarjeta cambia el detalle y la URL, sin volver a pedir nada", async () => {
    const api = await abrir();
    const lista = await tarjetas();
    await userEvent.click(lista[1] as HTMLElement);
    expect(tituloDelDetalle()).toBe(`Ruta B${B.polo.nombre}`);
    expect(window.location.hash).toBe("#/ruta/2");
    expect((await tarjetas())[1]?.getAttribute("aria-current")).toBe("true");
    expect(pedidosA(api, "/v1/viajes")).toHaveLength(1);
  });

  it("un enlace con #/ruta/3 abre la tercera", async () => {
    await abrir(`/?${CONSULTA}#/ruta/3`);
    await tarjetas();
    expect(tituloDelDetalle()).toBe(`Ruta C${RESPUESTA.rutas[2]?.polo.nombre}`);
  });

  it("la consulta se ve como chips, y quitar uno pide otra consulta", async () => {
    const api = await abrir();
    await tarjetas();
    const chips = within(screen.getByRole("list", { name: "Tu consulta" })).getAllByRole("listitem");
    expect(chips.map((c) => plano(c.textContent))).toEqual([
      "Desde Lima",
      "4 días",
      "Julio",
      "Historia y arqueología",
      "Naturaleza",
      "Hasta S/ 700",
      "Hasta 3 500 m",
      "Editar",
    ]);
    // El mes es obligatorio: no se puede quitar.
    expect(screen.queryByRole("link", { name: conNombre("Quitar: Julio") })).toBeNull();

    await userEvent.click(screen.getByRole("link", { name: conNombre("Quitar: Hasta S/ 700") }));
    await waitFor(() => expect(pedidosA(api, "/v1/viajes")).toHaveLength(2));
    expect(pedidosA(api, "/v1/viajes")[1]).toBe(
      "/v1/viajes?origen=lima&mes=7&dias=4&intereses=historia&intereses=naturaleza&altitud_max=3500",
    );
    await waitFor(() =>
      expect(screen.queryByRole("link", { name: conNombre("Quitar: Hasta S/ 700") })).toBeNull(),
    );
  });

  it("le pone a la URL la versión de datos con que se calculó", async () => {
    await abrir();
    await tarjetas();
    await waitFor(() => expect(window.location.search).toBe(`?${CONSULTA}&v=${VERSION}`));
    expect(screen.queryByText(/Este enlace se armó con los datos/)).toBeNull();
  });

  it("si el enlace es de otra versión de datos, lo dice", async () => {
    await abrir(`/?${CONSULTA}&v=2026.9.1`);
    await tarjetas();
    const aviso = screen.getByText(/Este enlace se armó con los datos/);
    expect(aviso.textContent).toContain(`2026.9.1`);
    expect(aviso.textContent).toContain(VERSION);

    await userEvent.click(screen.getByRole("link", { name: "Entendido" }));
    expect(screen.queryByText(/Este enlace se armó con los datos/)).toBeNull();
    expect(new URLSearchParams(window.location.search).get("v")).toBe(VERSION);
  });

  // Un enlace de antes de que se publicara nada, y uno de cuando había otros eventos.
  it.each([VERSION, `${VERSION}-e0000000`])(
    "si solo cambiaron los eventos publicados (enlace con %s), no avisa y pone la versión vigente",
    async (delEnlace) => {
      const vigente = `${VERSION}-e3f9a1c`;
      await abrir(`/?${CONSULTA}&v=${delEnlace}`, {
        "/v1/viajes": (url: URL) => ({ cuerpo: { ...viajesPara(url), version_datos: vigente } }),
      });
      await tarjetas();
      await waitFor(() => expect(new URLSearchParams(window.location.search).get("v")).toBe(vigente));
      expect(screen.queryByText(/Este enlace se armó con los datos/)).toBeNull();
    },
  );

  it("si cambiaron los artefactos, avisa aunque el enlace traiga la huella de los eventos", async () => {
    await abrir(`/?${CONSULTA}&v=2026.9.1-e3f9a1c`, {
      "/v1/viajes": (url: URL) => ({ cuerpo: { ...viajesPara(url), version_datos: `${VERSION}-e3f9a1c` } }),
    });
    await tarjetas();
    expect(screen.getByText(/Este enlace se armó con los datos/).textContent).toContain("2026.9.1-e3f9a1c");
  });

  it("sin rutas, dice por qué y ofrece lo que el motor sugiere", async () => {
    const api = await abrir(`/?origen=lima&mes=7&dias=1&altitud_max=0`, {
      "/v1/viajes": (url) =>
        url.searchParams.has("altitud_max")
          ? {
              cuerpo: {
                ...viajesPara(url),
                rutas: [],
                sin_resultado: {
                  motivo:
                    "En un día no se llega desde Lima a ninguna parada que cumpla lo que pediste y volver.",
                  sugerencias: [{ campo: "altitud_max", valor: null, efecto: "aparecen 3 rutas" }],
                },
              },
            }
          : { cuerpo: viajesPara(url) },
    });
    expect(await screen.findByText("No hay rutas para esta consulta")).toBeDefined();
    expect(screen.getByText(/En un día no se llega desde Lima/)).toBeDefined();
    expect(screen.getByText("aparecen 3 rutas")).toBeDefined();
    expect(screen.queryByRole("list", { name: "Rutas propuestas" })).toBeNull();

    await userEvent.click(screen.getByRole("link", { name: "Quitar el límite de altitud" }));
    expect(await tarjetas()).toHaveLength(3);
    expect(pedidosA(api, "/v1/viajes").at(-1)).toBe("/v1/viajes?origen=lima&mes=7&dias=1");
  });

  it("si la consulta no vale, muestra qué campo corregir", async () => {
    await abrir("/?origen=lima&mes=7&dias=20", {
      "/v1/viajes": {
        estado: 422,
        cuerpo: {
          detail: [{ campo: "dias", mensaje: "Debe ser menor o igual que 14.", tipo: "less_than_equal" }],
        },
      },
    });
    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("Hay algo que corregir en la consulta");
    expect(alerta.textContent).toContain("Días: Debe ser menor o igual que 14.");
    expect(within(alerta).queryByRole("button", { name: "Volver a intentar" })).toBeNull();

    await userEvent.click(within(alerta).getByRole("link", { name: "Revisar la consulta" }));
    expect(await screen.findByRole("heading", { level: 1, name: "¿Qué viaje quieres hacer?" })).toBeDefined();
  });

  it("sin conexión lo dice, y al reintentar sigue", async () => {
    let caido = true;
    await abrir(`/?${CONSULTA}`, {
      "/v1/viajes": (url) => {
        if (caido) throw new TypeError("Failed to fetch");
        return { cuerpo: viajesPara(url) };
      },
    });
    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("No hay conexión con el servidor");
    caido = false;
    await userEvent.click(within(alerta).getByRole("button", { name: "Volver a intentar" }));
    expect(await tarjetas()).toHaveLength(3);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("guardar, compartir e imprimir", () => {
  it("guarda el viaje en el navegador y lo lista en «Mis viajes»", async () => {
    await abrir();
    await tarjetas();
    const guardar = screen.getByRole("button", { name: "Guardar" });
    expect(guardar.getAttribute("aria-pressed")).toBe("false");
    await userEvent.click(guardar);
    expect(screen.getByRole("button", { name: "Guardado" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText("Guardado en Mis viajes, en este navegador.")).toBeDefined();
    expect(leerViajes()).toHaveLength(1);
    expect(leerViajes()[0]).toMatchObject({
      version: VERSION,
      consulta: { origen: "lima", mes: 7, dias: 4 },
    });

    await userEvent.click(screen.getByRole("link", { name: "Mis viajes" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Mis viajes" })).toBeDefined();
    const guardado = screen.getByRole("link", { name: /Lima · julio · 4.días/ });
    expect(guardado.getAttribute("href")).toBe(`?${CONSULTA}&v=${VERSION}`);

    // El enlace guardado vuelve al mismo viaje.
    await userEvent.click(guardado);
    await tarjetas();
    expect(screen.getByRole("button", { name: "Guardado" })).toBeDefined();

    await userEvent.click(screen.getByRole("link", { name: "Mis viajes" }));
    await userEvent.click(await screen.findByRole("button", { name: /^Quitar Lima/ }));
    expect(screen.getByText(/Todavía no guardaste ningún viaje/)).toBeDefined();
    expect(leerViajes()).toEqual([]);
  });

  it("comparte el enlace completo: la consulta, la versión y la ruta abierta", async () => {
    const usuario = userEvent.setup();
    await abrir();
    const lista = await tarjetas();
    await usuario.click(lista[1] as HTMLElement);
    await usuario.click(screen.getByRole("button", { name: "Compartir" }));
    expect(await screen.findByText(/Enlace copiado/)).toBeDefined();
    expect(await window.navigator.clipboard.readText()).toBe(
      `${window.location.origin}/?${CONSULTA}&v=${VERSION}#/ruta/2`,
    );
  });

  it("si el navegador no deja copiar, muestra el enlace para copiarlo a mano", async () => {
    await abrir();
    await tarjetas();
    vi.stubGlobal("navigator", { ...window.navigator, clipboard: undefined, share: undefined });
    await userEvent.click(screen.getByRole("button", { name: "Compartir" }));
    const enlace = await screen.findByRole("textbox", { name: "Enlace del viaje" });
    expect(enlace).toHaveProperty("value", `${window.location.origin}/?${CONSULTA}&v=${VERSION}`);
  });

  it("antes de imprimir abre lo plegado, que si no, no sale en el papel", async () => {
    await abrir();
    await tarjetas();
    const imprimir = vi.fn();
    vi.stubGlobal("print", imprimir);
    expect([...document.querySelectorAll("details")].some((d) => d.open)).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "Imprimir" }));
    expect(imprimir).toHaveBeenCalledOnce();
    expect([...document.querySelectorAll("details")].every((d) => d.open)).toBe(true);
  });
});

describe("el mapa y el itinerario", () => {
  it("«Ver el día en el mapa» lleva el mapa a ese día, y el selector lo devuelve a todo el viaje", async () => {
    await abrir();
    await tarjetas();
    const mapa = await screen.findByTestId("mapa");
    expect(mapa.dataset.dia).toBe("null");

    const conParadas = A.dias.filter((d) => (d.paradas ?? []).length > 0);
    const segundo = conParadas[1];
    if (!segundo) throw new Error("La primera ruta del ejemplo tiene paradas en un solo día.");
    await userEvent.click(screen.getByRole("button", { name: `Ver el día ${segundo.numero} en el mapa` }));
    expect(screen.getByTestId("mapa").dataset.dia).toBe(String(segundo.numero));
    expect(screen.getByRole("radio", { name: `Día ${segundo.numero}` })).toHaveProperty("checked", true);

    await userEvent.click(screen.getByRole("radio", { name: "Todo el viaje" }));
    expect(screen.getByTestId("mapa").dataset.dia).toBe("null");
    // Solo se ofrecen los días que tienen paradas.
    expect(screen.getAllByRole("radio", { name: /^Día \d+$/ })).toHaveLength(conParadas.length);
  });

  it("al cambiar de ruta el mapa vuelve a todo el viaje", async () => {
    await abrir();
    const lista = await tarjetas();
    await screen.findByTestId("mapa");
    const primerDia = A.dias.find((d) => (d.paradas ?? []).length > 0);
    await userEvent.click(screen.getByRole("button", { name: `Ver el día ${primerDia?.numero} en el mapa` }));
    await userEvent.click(lista[1] as HTMLElement);
    const mapa = await screen.findByTestId("mapa");
    expect(mapa.dataset.dia).toBe("null");
    expect(mapa.dataset.puntos).toBe(String(B.indicadores.paradas));
  });
});
