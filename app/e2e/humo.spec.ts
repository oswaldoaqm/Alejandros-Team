// Prueba de humo: lo que un viajero hace en su celular, contra el API de verdad.
// No reemplaza a las pruebas de cada pieza (src/**/*.test.tsx): confirma que todo junto anda.

import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

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

const PANTALLAS = [
  ["el formulario", "./"],
  ["los resultados", "./?origen=lima&mes=7&dias=6&intereses=historia&presupuesto=1500&altitud_max=3800"],
  ["la ficha de un polo", "./#/polo/33"],
  ["el calendario", "./#/calendario"],
  ["cómo funciona", "./#/acerca"],
  ["mis viajes", "./#/mis-viajes"],
] as const;

for (const [nombre, direccion] of PANTALLAS) {
  test(`${nombre}: sin desborde a lo ancho ni fallas de accesibilidad que una máquina detecte`, async ({
    page,
  }) => {
    await page.goto(direccion);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator(".cargando")).toHaveCount(0);
    // El mapa llega aparte: se espera a que esté o a que se sepa que no hay.
    if (nombre === "los resultados") await expect(page.locator(".maplibregl-canvas")).toBeVisible();

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
