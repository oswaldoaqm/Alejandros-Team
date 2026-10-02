// Prueba de humo: lo que un viajero hace en su celular, contra el API de verdad.
// No reemplaza a las pruebas de cada pieza (src/**/*.test.tsx): confirma que todo junto anda.

import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";
import { CLAVE_DE_LA_PRUEBA } from "./clave";

const API = "http://localhost:8000";

// El fondo del mapa viene de OpenFreeMap. La prueba no depende de esa red: lo cambia por un
// fondo liso, y el resto del mapa (paradas, base, recorrido) se dibuja como siempre.
const FONDO_LISO = {
  version: 8,
  sources: {},
  layers: [{ id: "fondo", type: "background", paint: { "background-color": "#dfe6dc" } }],
};

test.beforeEach(async ({ context }) => {
  await context.route("https://tiles.openfreemap.org/**", (ruta) =>
    ruta.fulfill({
      contentType: "application/json",
      headers: { "access-control-allow-origin": "*" },
      body: JSON.stringify(FONDO_LISO),
    }),
  );
});

const tarjetas = (pagina: Page) => pagina.getByRole("list", { name: "Rutas propuestas" }).getByRole("link");
const nombres = (pagina: Page) => tarjetas(pagina).locator(".tarjeta__nombre").allInnerTexts();

test("de la consulta al itinerario, con su mapa y sus fichas", async ({ page }) => {
  await page.goto("./");
  await page.getByLabel("Punto de partida").selectOption("lima");
  await page.getByText("Historia y arqueología").click();
  await page.getByRole("radio", { name: "Julio" }).check({ force: true });
  await page.getByRole("button", { name: "Generar mis rutas" }).click();

  await expect(tarjetas(page)).toHaveCount(3);
  await expect(page).toHaveURL(/\?origen=lima&mes=7&dias=6&intereses=historia&v=\d{4}\.\d+\.\d+/);

  // Seis días pedidos, seis días en el itinerario; y cada parada, con su ficha oficial.
  await expect(page.getByRole("heading", { level: 4 })).toHaveCount(6);
  const paradas = await page.locator(".parada__numero").count();
  expect(paradas).toBeGreaterThan(0);
  const fichas = page.getByRole("link", { name: /Ficha oficial/ });
  await expect(fichas).toHaveCount(paradas);
  await expect(fichas.first()).toHaveAttribute("href", /^https:\/\/consultasenlinea\.mincetur\.gob\.pe\//);

  // El mapa se dibuja y lleva una marca por parada, más la base.
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await expect(page.locator(".maplibregl-marker.marcador:not(.marcador--base)")).toHaveCount(paradas);
  await expect(page.locator(".maplibregl-marker.marcador--base")).toHaveCount(1);

  // Otra ruta: cambia el detalle y el enlace.
  const segunda = await tarjetas(page).nth(1).locator(".tarjeta__nombre").innerText();
  await tarjetas(page).nth(1).click();
  await expect(page).toHaveURL(/#\/ruta\/2$/);
  await expect(page.getByRole("heading", { level: 2, name: /^Ruta B/ })).toContainText(
    segunda.split("\n").at(-1) ?? "",
  );
});

test("el enlace es el viaje: quien lo abre ve las mismas rutas", async ({ page, context }) => {
  await page.goto("./?origen=cusco&mes=8&dias=5&intereses=naturaleza#/ruta/2");
  await expect(tarjetas(page)).not.toHaveCount(0);
  await expect(page).toHaveURL(/&v=/);
  const detalle = await page.getByRole("heading", { level: 2, name: /^Ruta B/ }).innerText();

  const otra = await context.newPage();
  await otra.goto(page.url());
  await expect(tarjetas(otra)).not.toHaveCount(0);
  expect(await nombres(otra)).toEqual(await nombres(page));
  expect(await otra.getByRole("heading", { level: 2, name: /^Ruta B/ }).innerText()).toBe(detalle);
  await expect(otra.getByText(/Este enlace se armó con los datos/)).toHaveCount(0);
});

test("guardar un viaje lo deja en «Mis viajes» de este navegador", async ({ page }) => {
  await page.goto("./?origen=lima&mes=7&dias=3");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("button", { name: "Guardado" })).toBeVisible();
  await page.getByRole("link", { name: "Mis viajes" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Mis viajes" })).toBeFocused();
  await page.getByRole("link", { name: /Lima · julio · 3.días/ }).click();
  await expect(tarjetas(page)).not.toHaveCount(0);
});

test("la ficha de un polo y el calendario cargan del API", async ({ page }) => {
  await page.goto("./?origen=lima&mes=7&dias=6");
  await page.getByRole("link", { name: /Ver todo lo que hay en el polo/ }).click();
  await expect(page.getByRole("radio", { name: /^Julio:/ })).toBeChecked();
  await expect(page.getByRole("link", { name: /Ficha oficial/ })).toHaveCount(10);

  await page.getByRole("link", { name: "Volver a tus rutas" }).click();
  await expect(tarjetas(page)).not.toHaveCount(0);

  await page.getByRole("link", { name: "Fiestas" }).click();
  await expect(page.getByRole("heading", { level: 2 }).first()).toContainText(/eventos? en julio de \d{4}/);
  await expect(page.locator(".evento").first()).toBeVisible();
});

test("un municipio publica un evento, con su lugar, y sale en el calendario", async ({
  page,
  request,
}, info) => {
  // Si el API ya estaba corriendo, levantado a mano y sin esta clave, aquí no se puede publicar.
  const sonda = await request.post(`${API}/v1/eventos`, {
    headers: { "X-Clave-Publicador": CLAVE_DE_LA_PRUEBA },
    data: {},
  });
  test.skip(
    sonda.status() === 401 || sonda.status() === 403,
    "El API que está corriendo no tiene la clave de esta prueba: ciérralo y deja que la prueba levante el suyo.",
  );

  // Dentro de unas semanas: ni pasado ni más allá de los doce meses que se publican.
  const dia = (cuantos: number) =>
    new Date(Date.now() + cuantos * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const nombre = `Feria de la prueba de humo (${info.project.name})`;
  const entidad = "Municipalidad de la prueba de humo";

  // Sin animaciones, el mapa salta a la ciudad de la región en vez de ir de a poco.
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("./");
  await page.getByRole("link", { name: "Para municipios: publicar un evento" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Publicar un evento" })).toBeFocused();

  await page.getByLabel("Nombre del evento").fill(nombre);
  await page.getByLabel("Empieza").fill(dia(40));
  await page.getByLabel(/^Termina/).fill(dia(41));
  await page.getByLabel("Región").selectOption("Áncash");
  await page.getByLabel("Provincia").fill("Huaraz");
  await page.getByLabel("Distrito").fill("Huaraz");

  // El mapa quedó sobre Huaraz: un toque en su centro pone la marca ahí.
  const lienzo = page.locator(".mapa--elegir .maplibregl-canvas");
  await expect(lienzo).toBeVisible();
  await lienzo.click();
  await expect(page.locator(".maplibregl-marker.marcador--lugar")).toHaveCount(1);
  await expect(page.getByText(/^Marcado en \u22129,5\d+, \u221277,5\d+\.$/)).toBeVisible();

  await page.getByLabel("Entidad que publica").fill(entidad);
  await page.getByLabel("Clave de publicador").fill(CLAVE_DE_LA_PRUEBA);
  await page.getByRole("button", { name: "Publicar el evento" }).click();

  await expect(page.getByRole("heading", { level: 1, name: "Evento publicado" })).toBeFocused();
  await expect(page.getByText(/sale también en las rutas que duermen o paran a 10 km o menos/)).toBeVisible();
  await expect(page.locator(".evento")).toContainText(`Publicado por ${entidad}`);

  // Y está en el calendario de su mes, que se pide de nuevo al API.
  await page.getByRole("link", { name: /^Ver el calendario de / }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Fiestas y eventos" })).toBeVisible();
  await expect(page.locator(".evento", { hasText: nombre })).toContainText(
    `Huaraz, Huaraz · Áncash · Publicado por ${entidad}`,
  );
});

test("sin la clave correcta no se publica, y lo dice en la casilla de la clave", async ({ page }) => {
  await page.goto("./#/publicar");
  await page.getByLabel("Nombre del evento").fill("Feria que no se publica");
  await page
    .getByLabel("Empieza")
    .fill(new Date(Date.now() + 40 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10));
  await page.getByLabel("Región").selectOption("Cusco");
  await page.getByLabel("Provincia").fill("Cusco");
  await page.getByLabel("Distrito").fill("Cusco");
  await page.getByLabel("Entidad que publica").fill("Alguien sin permiso");
  await page.getByLabel("Clave de publicador").fill("esta-no-es-la-clave");
  await page.getByRole("button", { name: "Publicar el evento" }).click();

  const alerta = page.getByRole("alert");
  await expect(alerta).toContainText("No se publicó");
  await expect(alerta).toBeFocused();
  await expect(page.getByLabel("Clave de publicador")).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByLabel("Nombre del evento")).toHaveValue("Feria que no se publica");
});

const PANTALLAS = [
  ["el formulario", "./"],
  ["los resultados", "./?origen=lima&mes=7&dias=6&intereses=historia&presupuesto=1500&altitud_max=3800"],
  ["la ficha de un polo", "./#/polo/33"],
  ["el calendario", "./#/calendario"],
  ["cómo funciona", "./#/acerca"],
  ["mis viajes", "./#/mis-viajes"],
  ["publicar un evento", "./#/publicar"],
] as const;

for (const [nombre, direccion] of PANTALLAS) {
  test(`${nombre}: sin desborde a lo ancho ni fallas de accesibilidad que una máquina detecte`, async ({
    page,
  }) => {
    await page.goto(direccion);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator(".cargando")).toHaveCount(0);
    // El mapa llega aparte: se espera a que esté o a que se sepa que no hay.
    if (nombre === "los resultados" || nombre === "publicar un evento") {
      await expect(page.locator(".maplibregl-canvas")).toBeVisible();
    }

    const desborde = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(desborde, "la página no debe desplazarse a lo ancho").toBeLessThanOrEqual(0);

    // El mapa queda fuera de esta revisión: con muchas paradas juntas sus marcas se enciman, y
    // lo que dice cada una está también en el itinerario, que es la alternativa accesible.
    const informe = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .exclude(".maplibregl-canvas-container")
      .exclude(".maplibregl-control-container")
      .analyze();
    expect(informe.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length})`)).toEqual([]);
  });
}
