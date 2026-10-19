import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { leerViajes } from "../almacen";
import type { Ruta } from "../api/tipos";
import type { PropsDeMapa } from "../piezas/MapaRuta";
import { irA, pedidosA, ponerApi, RESPUESTA, VERSION, viajesPara } from "../pruebas/api";
import { plano } from "../pruebas/texto";
import { nombreDelViaje } from "../textos";

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
const [A, B, C] = RESPUESTA.rutas;
if (!A || !B || !C) throw new Error("El ejemplo del contrato trae menos de tres rutas.");

async function abrir(direccion = `/?${CONSULTA}`, rutas: Parameters<typeof ponerApi>[0] = {}) {
  irA(direccion);
  const api = ponerApi(rutas);
  render(<App />);
  return api;
}

async function tarjetas() {
  return within(await screen.findByRole("list", { name: "Viajes propuestos" })).getAllByRole("link");
}

/** El viaje abierto, cuando ya llegó: su título en la portada. */
async function viajeAbierto() {
  await screen.findByRole("link", { name: "Tus viajes" });
  return plano(screen.getByRole("heading", { level: 1 }).textContent);
}

describe("los tres viajes", () => {
  it("muestra los viajes para elegir, con lo que deciden: precio, tiempo de ida y clima", async () => {
    await abrir();
    const lista = await tarjetas();
    expect(lista).toHaveLength(3);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Tres viajes para ti");
    RESPUESTA.rutas.forEach((ruta, i) => {
      const texto = plano(lista[i]?.textContent);
      expect(texto).toContain(nombreDelViaje(ruta.polo.nombre).titulo);
      expect(texto).toContain("por persona");
      expect(texto).toContain(`desde ${ruta.traslado.desde}`);
      expect(texto).toContain("en julio");
    });
    expect(lista[0]?.getAttribute("href")).toBe(`?${CONSULTA}&v=${VERSION}#/ruta/1`);
  });

  it("dice la consulta en una frase y lo demás que se pidió", async () => {
    await abrir();
    await tarjetas();
    expect(plano(screen.getByText(/^Desde Lima/).textContent)).toBe("Desde Lima, 4 días en julio");
    expect(plano(screen.getByText(/^Historia y arqueología/).textContent)).toBe(
      "Historia y arqueología y Naturaleza, hasta S/ 700 por persona, hasta 3 500 m de altura",
    );
  });

  it("marca los viajes que están fuera del circuito cuando no lo están todos", async () => {
    // El primero, en el circuito; los otros dos, fuera, sea cual sea el ejemplo del contrato.
    await abrir(`/?${CONSULTA}`, {
      "/v1/viajes": (url: URL) => {
        const respuesta = viajesPara(url);
        const rutas = respuesta.rutas.map((r, i) => ({
          ...r,
          polo: { ...r.polo, fuera_del_circuito: i > 0 },
        }));
        return { cuerpo: { ...respuesta, rutas } };
      },
    });
    const lista = await tarjetas();
    const sellos = lista.map((t) => within(t).queryByText("Fuera del circuito") !== null);
    expect(sellos).toEqual([false, true, true]);
  });

  // Los `cuantos` primeros viajes del ejemplo, todos fuera de Lima y de Cusco.
  const soloFuera = (cuantos: number) => ({
    "/v1/viajes": (url: URL) => {
      const respuesta = viajesPara(url);
      const rutas = respuesta.rutas
        .slice(0, cuantos)
        .map((r) => ({ ...r, polo: { ...r.polo, fuera_del_circuito: true } }));
      return { cuerpo: { ...respuesta, rutas } };
    },
  });

  it("si ninguno pasa por Lima ni por Cusco, lo dice una vez arriba y no en cada tarjeta", async () => {
    await abrir(`/?${CONSULTA}`, soloFuera(3));
    expect(await tarjetas()).toHaveLength(3);
    expect(screen.getByText(/están fuera del circuito/).textContent).toContain("Los tres están fuera");
    expect(screen.queryByText("Fuera del circuito")).toBeNull();
  });

  it("con dos viajes no dice «los tres»", async () => {
    await abrir(`/?${CONSULTA}`, soloFuera(2));
    expect(await tarjetas()).toHaveLength(2);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Dos viajes para ti");
    const frase = screen.getByText(/están fuera del circuito/).textContent;
    expect(frase).toContain("Los dos están fuera");
    expect(frase).not.toContain("tres");
  });

  it("un viaje solo lleva su etiqueta: no hay frase que lo diga por él", async () => {
    await abrir(`/?${CONSULTA}`, soloFuera(1));
    const [unica] = await tarjetas();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Un viaje para ti");
    expect(screen.queryByText(/están fuera del circuito/)).toBeNull();
    expect(within(unica as HTMLElement).getByText("Fuera del circuito")).toBeDefined();
  });

  it("«Cambiar» lleva al formulario con la misma consulta", async () => {
    await abrir();
    await tarjetas();
    await userEvent.click(screen.getByRole("link", { name: "Cambiar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Cambia tu viaje" })).toBeDefined();
    expect(plano(screen.getByRole("button", { name: /^Qué te gusta/ }).textContent)).toContain(
      "Historia y arqueología y Naturaleza",
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

  it("sin viajes, dice por qué y ofrece lo que el motor sugiere", async () => {
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
                  sugerencias: [{ campo: "altitud_max", valor: null, efecto: "aparecen 3 viajes" }],
                },
              },
            }
          : { cuerpo: viajesPara(url) },
    });
    expect(await screen.findByRole("heading", { name: "No encontramos un viaje así" })).toBeDefined();
    expect(screen.getByText(/En un día no se llega desde Lima/)).toBeDefined();
    expect(screen.getByText("aparecen 3 viajes")).toBeDefined();
    expect(screen.queryByRole("list", { name: "Viajes propuestos" })).toBeNull();

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

    await userEvent.click(within(alerta).getByRole("link", { name: "Revisar el viaje" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Cambia tu viaje" })).toBeDefined();
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

describe("el viaje a una zona elegida", () => {
  const HUANCAYO = "origen=lima&destino=33&mes=7&dias=4";
  const CUZCO = "origen=lima&destino=36&mes=7&dias=4&solo_por_tierra=true";

  it("se abre directo, porque es uno solo, y «Cambiar el viaje» vuelve al formulario", async () => {
    const api = await abrir(`/?${HUANCAYO}`);
    await screen.findByRole("heading", { level: 1, name: "Huancayo" });
    await waitFor(() => expect(window.location.hash).toBe("#/ruta/1"));
    expect(window.location.search).toBe(`?${HUANCAYO}&v=${VERSION}`);
    expect(pedidosA(api, "/v1/viajes")).toEqual([`/v1/viajes?${HUANCAYO}`]);

    const cambiar = screen.getByRole("link", { name: "Cambiar el viaje" });
    expect(cambiar.getAttribute("href")).toBe(`?${HUANCAYO}&v=${VERSION}#/editar`);
    await userEvent.click(cambiar);
    await screen.findByRole("heading", { level: 1, name: "Cambia tu viaje" });
    await waitFor(() =>
      expect(plano(screen.getByRole("button", { name: /^A dónde/ }).textContent)).toBe("A dónde Huancayo"),
    );
  });

  it("si no cabe, dice por qué y qué cambiar: con el destino, el viaje se abre directo", async () => {
    await abrir(`/?${CUZCO}#/ruta/1`);
    expect(await screen.findByRole("heading", { level: 2, name: "Así no cabe" })).toBeDefined();
    // El nombre de la zona sale de la lista de zonas, que puede llegar después del viaje.
    expect(await screen.findByRole("heading", { level: 1, name: "Tu viaje a Cuzco" })).toBeDefined();
    expect(screen.getByText(/^En 4 días no da para ir de Lima a Cuzco y volver/)).toBeDefined();
    expect(screen.getByText("Con un cambio sí sale:")).toBeDefined();
    expect(plano(document.querySelector(".resultados__frase")?.textContent)).toBe(
      "De Lima a Cuzco, 4 días en julio",
    );
    expect(plano(document.title)).toBe("De Lima a Cuzco, 4 días en julio · DreemGO");

    const masDias = screen.getByRole("link", { name: /^Probar con 12.días$/ });
    expect(masDias.getAttribute("href")).toBe(
      `?origen=lima&destino=36&mes=7&dias=12&solo_por_tierra=true&v=${VERSION}#/ruta/1`,
    );
    expect(screen.getByText("sale el viaje, sin volar")).toBeDefined();
    const volando = screen.getByRole("link", { name: "Buscar también con vuelos" });
    expect(volando.getAttribute("href")).toBe(`?origen=lima&destino=36&mes=7&dias=4&v=${VERSION}#/ruta/1`);
    expect(screen.getByText("sale el viaje, con vuelo")).toBeDefined();
    const otras = screen.getByRole("link", { name: "Ver viajes a otras zonas" });
    expect(otras.getAttribute("href")).toBe(`?origen=lima&mes=7&dias=4&solo_por_tierra=true&v=${VERSION}`);
    await userEvent.click(otras);
    expect(await tarjetas()).toHaveLength(3);
  });
});

describe("un viaje abierto", () => {
  it("al tocar un viaje se abre su plan, sin volver a pedir nada", async () => {
    const api = await abrir();
    const lista = await tarjetas();
    await userEvent.click(lista[1] as HTMLElement);
    expect(await viajeAbierto()).toBe(nombreDelViaje(B.polo.nombre).titulo);
    expect(window.location.hash).toBe("#/ruta/2");
    expect(pedidosA(api, "/v1/viajes")).toHaveLength(1);
  });

  it("un enlace con #/ruta/3 abre el tercero", async () => {
    await abrir(`/?${CONSULTA}#/ruta/3`);
    expect(await viajeAbierto()).toBe(nombreDelViaje(C.polo.nombre).titulo);
  });

  it("«Tus viajes» vuelve a los tres", async () => {
    await abrir(`/?${CONSULTA}#/ruta/2`);
    await viajeAbierto();
    await userEvent.click(screen.getByRole("link", { name: "Tus viajes" }));
    expect(await tarjetas()).toHaveLength(3);
    expect(window.location.hash).toBe("");
  });

  it("dice por qué te va a gustar sin repetir lo que ya está arriba", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    const razones = within(screen.getByRole("region", { name: "Por qué te va a gustar" }))
      .getAllByRole("listitem")
      .map((r) => plano(r.textContent));
    expect(razones[0]).toBe(
      "2 imperdibles: Santuario Arqueológico de Wariwillka y Convento de Santa Rosa de Ocopa.",
    );
    // El clima ya está en los datos de arriba, y la jerarquía, en los imperdibles.
    expect(razones.some((r) => /temporada seca|jerarquía/.test(r))).toBe(false);
    expect(razones).toContain("Todas sus paradas son de historia y arqueología o naturaleza.");
  });

  it("pone los avisos antes de ir, y el de los datos en la letra chica", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    const antes = screen.getByRole("region", { name: "Antes de ir" });
    for (const aviso of (A.avisos ?? []).filter((a) => a.tipo !== "datos")) {
      expect(plano(antes.textContent)).toContain(plano(aviso.mensaje));
    }
    const datos = (A.avisos ?? []).find((a) => a.tipo === "datos");
    if (datos) expect(plano(antes.textContent)).not.toContain(plano(datos.mensaje));
    for (const linea of RESPUESTA.atribucion) expect(screen.getByText(linea)).toBeDefined();
    expect(screen.getByText(A.estacionalidad.explicacion)).toBeDefined();
  });

  it("un viaje con vuelo lo dice en su tarjeta, en sus datos y en su costo", async () => {
    const conVuelo = {
      "/v1/viajes": (url: URL) => {
        const respuesta = viajesPara(url);
        const [primera, ...resto] = respuesta.rutas;
        if (!primera) throw new Error("El ejemplo del contrato no trae rutas.");
        const enAvion: Ruta = {
          ...primera,
          traslado: {
            ...primera.traslado,
            horas: 4.5,
            medios: ["avion", "carretera"],
            vuelos: [
              { desde: "Lima", hasta: "Cusco", codigo_desde: "LIM", codigo_hasta: "CUZ", horas: 1.33 },
            ],
            fuente: "red_vial_y_vuelos",
          },
          costo: {
            ...primera.costo,
            desglose: { transporte: 227, vuelos: 527, alojamiento: 398, alimentacion: 341, entradas: 250 },
          },
        };
        return { cuerpo: { ...respuesta, rutas: [enAvion, ...resto] } };
      },
    };
    await abrir(`/?${CONSULTA}`, conVuelo);
    const [primera] = await tarjetas();
    expect(plano(primera?.textContent)).toContain("4 h 30 desde Lima, con vuelo");
    await userEvent.click(primera as HTMLElement);
    await viajeAbierto();
    expect(screen.getByText("desde Lima, con vuelo")).toBeDefined();
    const costo = within(screen.getByRole("region", { name: "Cuánto cuesta" }));
    expect(
      costo
        .getAllByRole("listitem")
        .slice(0, 2)
        .map((li) => plano(li.textContent)),
    ).toEqual(["TransporteS/ 227", "VuelosS/ 527"]);
  });

  it("un viaje en bus de noche lo dice en su tarjeta, en sus datos y antes de ir", async () => {
    // En el ejemplo del contrato, Trujillo: 11 horas desde Lima, en bus de noche.
    const conBus = RESPUESTA.rutas.findIndex((r) => r.traslado.bus_de_noche);
    const ruta = RESPUESTA.rutas[conBus];
    if (!ruta?.traslado.bus_de_noche)
      throw new Error("El ejemplo del contrato no trae un viaje en bus de noche.");
    await abrir(`/?${CONSULTA}`);
    const tarjeta = (await tarjetas())[conBus];
    expect(plano(tarjeta?.textContent)).toContain("desde Lima, en bus de noche");
    await userEvent.click(tarjeta as HTMLElement);
    await viajeAbierto();
    expect(screen.getByText("desde Lima, en bus de noche")).toBeDefined();
    const antes = screen.getByRole("region", { name: "Antes de ir" });
    expect(plano(antes.textContent)).toContain(
      `sales de Lima a las ${ruta.traslado.bus_de_noche.sale} la noche antes del día 1`,
    );
  });

  it("el plan va de a un día, y el mapa sigue al día elegido", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    const mapa = await screen.findByTestId("mapa");
    expect(mapa.dataset.dia).toBe("null");
    expect(mapa.dataset.puntos).toBe(String(A.indicadores.paradas));
    expect(mapa.dataset.base).toBe(A.polo.base.nombre);

    // Todo el viaje: un renglón por día.
    expect(screen.getAllByRole("button", { name: /^Día \d/ })).toHaveLength(A.dias.length);
    await userEvent.click(screen.getByRole("button", { name: /^Día 2/ }));
    expect(screen.getByTestId("mapa").dataset.dia).toBe("2");
    expect(screen.getByRole("radio", { name: "Día 2" })).toHaveProperty("checked", true);
    const lugares = within(screen.getByRole("list", { name: "Lugares del día 2" })).getAllByRole("button");
    expect(lugares.length).toBeGreaterThan(0);

    await userEvent.click(screen.getByRole("radio", { name: "Todo" }));
    expect(screen.getByTestId("mapa").dataset.dia).toBe("null");
  });

  it("al tocar un lugar se abre su hoja con la ficha oficial", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    // El primer día con lugares: el de llegada puede ser de solo viaje.
    const dia = A.dias.find((d) => (d.paradas ?? []).length > 0);
    const primera = dia?.paradas?.[0];
    if (!dia || !primera) throw new Error("El viaje del ejemplo no tiene ningún día con paradas.");
    await userEvent.click(screen.getByRole("radio", { name: `Día ${dia.numero}` }));
    await userEvent.click(screen.getByRole("button", { name: new RegExp(primera.recurso.nombre) }));
    const hoja = screen.getByRole("dialog", { name: primera.recurso.nombre });
    expect(
      within(hoja)
        .getByRole("link", { name: /Ver la ficha oficial/ })
        .getAttribute("href"),
    ).toBe(primera.recurso.url_ficha);
  });
});

describe("guardar, compartir e imprimir", () => {
  it("guarda el viaje abierto en el navegador, y Guardados vuelve a ese viaje", async () => {
    await abrir(`/?${CONSULTA}#/ruta/2`);
    const nombre = await viajeAbierto();
    const guardar = screen.getByRole("button", { name: "Guardar" });
    expect(guardar.getAttribute("aria-pressed")).toBe("false");
    await userEvent.click(guardar);
    expect(screen.getByRole("button", { name: "Guardado" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText("Guardado en este navegador.")).toBeDefined();
    expect(leerViajes()).toHaveLength(1);
    expect(leerViajes()[0]).toMatchObject({
      ruta: 2,
      titulo: B.polo.nombre,
      version: VERSION,
      consulta: { origen: "lima", mes: 7, dias: 4 },
    });

    const [enLaCabecera] = screen.getAllByRole("link", { name: "Guardados" });
    await userEvent.click(enLaCabecera as HTMLElement);
    expect(await screen.findByRole("heading", { level: 1, name: "Guardados" })).toBeDefined();
    // Se reconoce por su nombre, y debajo dice lo que se pidió.
    const guardado = screen.getByRole("link", { name: new RegExp(`^${B.polo.nombre}`) });
    expect(plano(guardado.textContent)).toContain("Desde Lima, 4 días en julio");
    expect(guardado.getAttribute("href")).toBe(`?${CONSULTA}&v=${VERSION}#/ruta/2`);

    // El enlace guardado abre el mismo viaje, no los tres.
    await userEvent.click(guardado);
    expect(await viajeAbierto()).toBe(nombre);
    expect(screen.getByRole("button", { name: "Guardado" })).toBeDefined();

    await userEvent.click(screen.getAllByRole("link", { name: "Guardados" })[0] as HTMLElement);
    await userEvent.click(
      await screen.findByRole("button", { name: new RegExp(`^Quitar ${B.polo.nombre}`) }),
    );
    expect(screen.getByText("Todavía no guardaste ningún viaje")).toBeDefined();
    expect(leerViajes()).toEqual([]);
  });

  it("guardar un viaje no da por guardados los otros dos", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    await userEvent.click(screen.getByRole("link", { name: "Tus viajes" }));
    await userEvent.click((await tarjetas())[2] as HTMLElement);
    await viajeAbierto();
    expect(screen.getByRole("button", { name: "Guardar" }).getAttribute("aria-pressed")).toBe("false");
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(leerViajes().map((v) => [v.titulo, v.ruta])).toEqual([
      [C.polo.nombre, 3],
      [A.polo.nombre, 1],
    ]);
  });

  it("lo guardado cuando no se elegía un viaje sigue abriendo los tres", async () => {
    localStorage.setItem(
      "dreemgo.viajes.v1",
      JSON.stringify([
        {
          consulta: {
            origen: "lima",
            mes: 7,
            fecha_inicio: null,
            dias: 4,
            intereses: [],
            presupuesto: null,
            altitud_max: null,
            sorpresa: false,
          },
          version: VERSION,
          titulo: "Desde Lima, 4 días en julio",
          guardado: "2026-10-01T10:00:00Z",
        },
      ]),
    );
    await abrir("/#/mis-viajes");
    const guardado = await screen.findByRole("link", { name: /^Desde Lima, 4.días en julio/ });
    expect(guardado.getAttribute("href")).toBe(`?origen=lima&mes=7&dias=4&v=${VERSION}`);
    await userEvent.click(guardado);
    expect(await tarjetas()).toHaveLength(3);
  });

  it("comparte el enlace completo: la consulta, la versión y el viaje abierto", async () => {
    const usuario = userEvent.setup();
    await abrir(`/?${CONSULTA}#/ruta/2`);
    await viajeAbierto();
    await usuario.click(screen.getByRole("button", { name: "Compartir" }));
    expect(await screen.findByText(/Enlace copiado/)).toBeDefined();
    await waitFor(async () =>
      expect(await window.navigator.clipboard.readText()).toBe(
        `${window.location.origin}/?${CONSULTA}&v=${VERSION}#/ruta/2`,
      ),
    );
  });

  it("si el navegador no deja copiar, muestra el enlace para copiarlo a mano", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    vi.stubGlobal("navigator", { ...window.navigator, clipboard: undefined, share: undefined });
    await userEvent.click(screen.getByRole("button", { name: "Compartir" }));
    const enlace = await screen.findByRole("textbox", { name: "Enlace del viaje" });
    expect(enlace).toHaveProperty("value", `${window.location.origin}/?${CONSULTA}&v=${VERSION}#/ruta/1`);
  });

  it("antes de imprimir abre lo plegado, que si no, no sale en el papel", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    const imprimir = vi.fn();
    vi.stubGlobal("print", imprimir);
    expect([...document.querySelectorAll("details")].some((d) => d.open)).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "Imprimir o guardar en PDF" }));
    expect(imprimir).toHaveBeenCalledOnce();
    expect([...document.querySelectorAll("details")].every((d) => d.open)).toBe(true);
  });

  it("en papel va el plan completo, todos los días", async () => {
    await abrir(`/?${CONSULTA}#/ruta/1`);
    await viajeAbierto();
    const impreso = document.querySelector(".plan-impreso");
    expect(impreso?.querySelectorAll("h3")).toHaveLength(A.dias.length);
    // Cada lugar y, entre ellos, el almuerzo de cada día que lo tiene.
    const almuerzos = A.dias.filter((d) => d.almuerzo && (d.paradas ?? []).length > 0).length;
    expect(almuerzos).toBeGreaterThan(0);
    expect(impreso?.querySelectorAll("li")).toHaveLength(A.indicadores.paradas + almuerzos);
    const lineas = [...(impreso?.querySelectorAll("li") ?? [])].map((li) => plano(li.textContent));
    expect(lineas.filter((l) => / Almuerzo\. /.test(l))).toHaveLength(almuerzos);
  });
});
