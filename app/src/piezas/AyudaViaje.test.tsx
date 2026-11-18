import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";
import { App } from "../App";
import { permitirEstadisticas } from "../analitica";
import { irA, type PedidoRecibido, pedidosA, ponerApi, viajesPara } from "../pruebas/api";

it("busca viajes reales desde el chat y muestra también las advertencias del motor", async () => {
  irA("/#/planear");
  const api = ponerApi({
    "/v1/viajes": (url) => {
      const respuesta = viajesPara(url);
      return {
        cuerpo: {
          ...respuesta,
          rutas: respuesta.rutas.map((ruta, indice) =>
            indice === 0
              ? {
                  ...ruta,
                  avisos: [
                    ...(ruta.avisos ?? []),
                    {
                      tipo: "datos",
                      nivel: "advertencia",
                      mensaje: "No incluye paradas de playa.",
                    },
                  ],
                }
              : ruta,
          ),
        },
      };
    },
  });
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");
  await usuario.type(
    within(dialogo).getByLabelText("Escribe tu pregunta"),
    "Quiero playa desde Lima en julio, 4 días",
  );
  await usuario.click(within(dialogo).getByRole("button", { name: "Preguntar" }));

  expect(await within(dialogo).findByText("Atención: No incluye paradas de playa.")).toBeDefined();
  const consultas = pedidosA(api, "/v1/viajes");
  expect(consultas).toHaveLength(1);
  const parametros = new URL(consultas[0] ?? "", "http://localhost").searchParams;
  expect(parametros.get("origen")).toBe("lima");
  expect(parametros.get("mes")).toBe("7");
  expect(parametros.get("dias")).toBe("4");
  expect(parametros.getAll("intereses")).toEqual(["playa"]);
  expect(within(dialogo).getAllByRole("link", { name: /Ver este itinerario/ }).length).toBeGreaterThan(0);
  expect(pedidosA(api, "/v1/comentarios", "POST")).toEqual([]);
});

it("responde una pregunta escrita con la guía existente sin enviar datos al servidor", async () => {
  irA("/#/planear");
  const api = ponerApi();
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");

  await usuario.type(within(dialogo).getByLabelText("Escribe tu pregunta"), "¿Cuánto costará mi viaje?");
  await usuario.click(within(dialogo).getByRole("button", { name: "Preguntar" }));

  expect(within(dialogo).getByText("¿Cuánto costará mi viaje?")).toBeDefined();
  expect(
    within(dialogo).getByText("No. El viaje muestra un rango estimado por persona para orientarte.", {
      exact: false,
    }),
  ).toBeDefined();
  expect(pedidosA(api, "/v1/comentarios", "POST")).toEqual([]);
  expect(pedidosA(api, "/v1/analitica/eventos", "POST")).toEqual([]);
});

it("cuenta el uso de la ayuda con permiso sin transmitir preguntas ni comentarios", async () => {
  irA("/");
  permitirEstadisticas(false);
  const api = ponerApi({
    "/v1/comentarios": {
      estado: 201,
      cuerpo: { id: "f85ed665-d6d3-4b31-a20b-f6729c07a760", estado: "recibido" },
    },
  });
  permitirEstadisticas(true);
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");
  await usuario.type(within(dialogo).getByLabelText("Escribe tu pregunta"), "¿Puedo llevar mascotas?");
  await usuario.click(within(dialogo).getByRole("button", { name: "Preguntar" }));
  await usuario.click(within(dialogo).getByRole("button", { name: "Dejar este mensaje" }));
  await usuario.click(within(dialogo).getByRole("button", { name: "Enviar mensaje" }));
  await within(dialogo).findByText("Recibimos tu mensaje. Gracias por ayudarnos a mejorar DreemGO.");

  const eventos = api.mock.calls
    .filter(
      ([url, opciones]) =>
        new URL(String(url)).pathname === "/v1/analitica/eventos" && opciones?.method === "POST",
    )
    .map(([, opciones]) => JSON.parse(String(opciones?.body)) as Record<string, unknown>);
  expect(eventos.map((evento) => evento.tipo)).toEqual([
    "sesion_iniciada",
    "ayuda_consultada",
    "comentario_enviado",
  ]);
  for (const evento of eventos) {
    expect(Object.keys(evento).sort()).toEqual(["id_evento", "sesion", "tipo"]);
    expect(JSON.stringify(evento)).not.toContain("mascotas");
  }
  permitirEstadisticas(false);
});

it("deriva una pregunta desconocida al formulario sin enviarla por sí sola", async () => {
  irA("/");
  const api = ponerApi();
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");

  await usuario.type(
    within(dialogo).getByLabelText("Escribe tu pregunta"),
    "¿Tienen descuento para estudiantes?",
  );
  await usuario.click(within(dialogo).getByRole("button", { name: "Preguntar" }));
  expect(
    within(dialogo).getByText("Aún no tenemos una respuesta preparada para esa duda.", { exact: false }),
  ).toBeDefined();
  expect(pedidosA(api, "/v1/comentarios", "POST")).toEqual([]);

  await usuario.click(within(dialogo).getByRole("button", { name: "Dejar este mensaje" }));
  expect((within(dialogo).getByLabelText("Tu mensaje") as HTMLTextAreaElement).value).toBe(
    "¿Tienen descuento para estudiantes?",
  );
  expect(pedidosA(api, "/v1/comentarios", "POST")).toEqual([]);
});

it("orienta desde el formulario y recibe un comentario sin pedir datos personales", async () => {
  irA("/#/planear");
  const recibidos: PedidoRecibido[] = [];
  const api = ponerApi({
    "/v1/comentarios": (_url, pedido) => {
      recibidos.push(pedido);
      return { estado: 201, cuerpo: { id: "f85ed665-d6d3-4b31-a20b-f6729c07a760", estado: "recibido" } };
    },
  });
  render(<App />);
  const usuario = userEvent.setup();

  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");
  await usuario.click(within(dialogo).getByRole("button", { name: "¿El costo es un precio final?" }));
  expect(
    within(dialogo).getByText("No. El viaje muestra un rango estimado por persona para orientarte.", {
      exact: false,
    }),
  ).toBeDefined();
  await usuario.click(
    within(dialogo).getByRole("button", { name: "¿Cómo consideran el clima y la altura?" }),
  );
  expect(within(dialogo).getByText("no es un pronóstico diario", { exact: false })).toBeDefined();

  await usuario.click(within(dialogo).getByRole("button", { name: "Déjanos un mensaje" }));
  expect(within(dialogo).queryByLabelText(/nombre|correo/i)).toBeNull();
  await usuario.selectOptions(within(dialogo).getByLabelText("¿Sobre qué nos escribes?"), "sugerencia");
  await usuario.type(
    within(dialogo).getByLabelText("Tu mensaje"),
    "Me gustaría comparar dos rutas de forma más clara.",
  );
  await usuario.click(within(dialogo).getByRole("button", { name: "Enviar mensaje" }));

  expect(
    await within(dialogo).findByText("Recibimos tu mensaje. Gracias por ayudarnos a mejorar DreemGO."),
  ).toBeDefined();
  const recibido = recibidos[0];
  if (!recibido) throw new Error("No llegó el comentario al API.");
  expect(recibido.metodo).toBe("POST");
  expect(recibido.cuerpo).toMatchObject({
    categoria: "sugerencia",
    mensaje: "Me gustaría comparar dos rutas de forma más clara.",
  });
  expect((recibido.cuerpo as { sesion: string }).sesion).toMatch(/^[0-9a-f-]{36}$/i);
  expect(api).toHaveBeenCalled();
});

it("mantiene el texto cuando el servidor limita los mensajes de una sesión", async () => {
  irA("/");
  ponerApi({
    "/v1/comentarios": { estado: 429, cuerpo: { detail: "Demasiados mensajes." } },
  });
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");
  await usuario.click(within(dialogo).getByRole("button", { name: "Déjanos un mensaje" }));
  const caja = within(dialogo).getByLabelText("Tu mensaje");
  await usuario.type(caja, "No encuentro la ruta que buscaba.");
  await usuario.click(within(dialogo).getByRole("button", { name: "Enviar mensaje" }));
  expect((await within(dialogo).findByRole("alert")).textContent).toContain("tres mensajes de esta sesión");
  expect((caja as HTMLTextAreaElement).value).toBe("No encuentro la ruta que buscaba.");
});

it("conserva varias preguntas en la conversación y permite borrarla", async () => {
  irA("/");
  const api = ponerApi();
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");

  await usuario.click(within(dialogo).getByRole("button", { name: "¿Cómo empiezo a planear?" }));
  await usuario.click(within(dialogo).getByRole("button", { name: "¿Puedo elegir un destino concreto?" }));
  const conversacion = within(dialogo).getByRole("log", { name: "Conversación de ayuda" });
  expect(within(conversacion).getByText("¿Cómo empiezo a planear?")).toBeDefined();
  expect(within(conversacion).getByText("¿Puedo elegir un destino concreto?")).toBeDefined();
  expect(within(conversacion).getByText("Si no cabe con tus días", { exact: false })).toBeDefined();

  await usuario.click(within(dialogo).getByRole("button", { name: "Borrar conversación" }));
  expect(within(conversacion).queryByText("¿Puedo elegir un destino concreto?")).toBeNull();
  expect(within(conversacion).getByText("Hola. Puedo orientarte", { exact: false })).toBeDefined();
  expect(pedidosA(api, "/v1/comentarios", "POST")).toEqual([]);
});

it("abre temas adicionales y deja la consulta sin respuesta lista para enviarse", async () => {
  irA("/");
  const api = ponerApi();
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");
  await usuario.click(within(dialogo).getByRole("button", { name: "Ver todos los temas" }));
  await usuario.click(within(dialogo).getByRole("button", { name: "¿Puedo reservar desde la web?" }));
  expect(within(dialogo).getByText("no vende pasajes", { exact: false })).toBeDefined();
  await usuario.type(within(dialogo).getByLabelText("Escribe tu pregunta"), "¿Puedo llevar mascotas?");
  await usuario.click(within(dialogo).getByRole("button", { name: "Preguntar" }));
  await usuario.click(within(dialogo).getByRole("button", { name: "Dejar este mensaje" }));
  expect((within(dialogo).getByLabelText("Tu mensaje") as HTMLTextAreaElement).value).toBe(
    "¿Puedo llevar mascotas?",
  );
  expect(pedidosA(api, "/v1/comentarios", "POST")).toEqual([]);
});

it("también interpreta vida nocturna como búsqueda de recomendaciones", async () => {
  irA("/");
  const api = ponerApi();
  render(<App />);
  const usuario = userEvent.setup();
  await usuario.click(screen.getByRole("button", { name: "Abrir ayuda de viaje" }));
  const dialogo = screen.getByRole("dialog");

  await usuario.type(
    within(dialogo).getByLabelText("Escribe tu pregunta"),
    "Quiero vida nocturna desde Lima en julio",
  );
  await usuario.click(within(dialogo).getByRole("button", { name: "Preguntar" }));

  await within(dialogo).findByText(/Consulta usada:/);
  const consultas = pedidosA(api, "/v1/viajes");
  expect(consultas).toHaveLength(1);
  const parametros = new URL(consultas[0] ?? "", "http://localhost").searchParams;
  expect(parametros.getAll("intereses")).toEqual(["vida_nocturna"]);
});
