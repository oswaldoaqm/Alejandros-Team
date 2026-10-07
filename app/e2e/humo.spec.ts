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

const tarjetas = (pagina: Page) => pagina.getByRole("list", { name: "Viajes propuestos" }).getByRole("link");
const titulo = (pagina: Page) => pagina.getByRole("heading", { level: 1 });

test("de la consulta al viaje, con su mapa, sus días y la ficha de cada lugar", async ({ page }) => {
  await page.goto("./");
  await page.getByLabel("Punto de partida").selectOption("lima");
  await page.getByText("Historia y arqueología").click();
  await page.getByRole("radio", { name: "Julio" }).check({ force: true });
  await page.getByRole("button", { name: "Generar mis rutas" }).click();

  await expect(tarjetas(page)).toHaveCount(3);
  await expect(page).toHaveURL(/\?origen=lima&mes=7&dias=6&intereses=historia&v=\d{4}\.\d+\.\d+/);

  // El primero: su portada, y el plan con un segmento por día. Seis días pedidos, seis en el plan.
  const nombre = await tarjetas(page).first().locator(".viaje-tarjeta__nombre").innerText();
  await tarjetas(page).first().click();
  await expect(page).toHaveURL(/#\/ruta\/1$/);
  await expect(titulo(page)).toHaveText(nombre.split("\n")[0] ?? "");
  await expect(page.getByRole("radio", { name: /^Día \d+$/ })).toHaveCount(6);

  // El mapa se dibuja con una marca por lugar, y la de donde se duerme.
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  const lugares = await page.locator(".maplibregl-marker.pin").count();
  expect(lugares).toBeGreaterThan(0);
  await expect(page.locator(".maplibregl-marker.pin-base")).toHaveCount(1);

  // Un día: solo sus lugares en el mapa, y cada uno abre su hoja con la ficha oficial.
  await page.getByRole("radio", { name: "Día 2" }).check({ force: true });
  const delDia = page.getByRole("list", { name: "Lugares del día 2" }).getByRole("button");
  await expect(delDia.first()).toBeVisible();
  await expect(page.locator(".maplibregl-marker.pin:not(.pin--oculto)")).toHaveCount(await delDia.count());
  await delDia.first().click();
  await expect(page.getByRole("dialog").getByRole("link", { name: /^Ver la ficha oficial/ })).toHaveAttribute(
    "href",
    /^https:\/\/consultasenlinea\.mincetur\.gob\.pe\//,
  );
  await page.getByRole("dialog").getByRole("button", { name: "Cerrar" }).click();

  // «Tus viajes» vuelve a los tres.
  await page.getByRole("link", { name: "Tus viajes" }).click();
  await expect(tarjetas(page)).toHaveCount(3);
});

test("el enlace es el viaje: quien lo abre ve el mismo", async ({ page, context }) => {
  await page.goto("./?origen=cusco&mes=8&dias=5&intereses=naturaleza#/ruta/2");
  await expect(page.getByRole("link", { name: "Tus viajes" })).toBeVisible();
  await expect(page).toHaveURL(/&v=/);
  const nombre = await titulo(page).innerText();
  const dias = await page.locator(".dia-fila").allInnerTexts();

  const otra = await context.newPage();
  await otra.goto(page.url());
  await expect(otra.getByRole("link", { name: "Tus viajes" })).toBeVisible();
  await expect(titulo(otra)).toHaveText(nombre);
  expect(await otra.locator(".dia-fila").allInnerTexts()).toEqual(dias);
  await expect(otra.getByText(/Este enlace se armó con los datos/)).toHaveCount(0);
});

test("guardar un viaje lo deja en «Guardados» de este navegador", async ({ page }) => {
  await page.goto("./?origen=lima&mes=7&dias=3#/ruta/1");
  // Exacto: «Imprimir o guardar en PDF» también dice «guardar».
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Guardado", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("link", { name: "Guardados" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Guardados" })).toBeFocused();
  await page.getByRole("link", { name: /Desde Lima, 3.días en julio/ }).click();
  await expect(tarjetas(page)).toHaveCount(3);
});

test("la zona de un viaje y el calendario cargan del API", async ({ page }) => {
  await page.goto("./?origen=lima&mes=7&dias=6#/ruta/1");
  await expect(page.getByRole("link", { name: "Tus viajes" })).toBeVisible();
  const nombre = await titulo(page).innerText();
  await page.getByRole("link", { name: /^Ver todos los lugares de la zona/ }).click();
  await expect(page.getByRole("radio", { name: /^Julio:/ })).toBeChecked();
  await expect(page.getByRole("region", { name: "Qué hay para ver" }).getByRole("listitem")).toHaveCount(8);

  await page.getByRole("link", { name: "Tus viajes" }).click();
  await expect(titulo(page)).toHaveText(nombre);

  // Exacto: el viaje también enlaza «Ver todas las fiestas de julio».
  await page.getByRole("link", { name: "Fiestas", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: /eventos? en julio de \d{4}/ })).toBeVisible();
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
  await page.getByRole("link", { name: "Publica un evento" }).click();
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
  const publicado = page.locator(".evento", { hasText: nombre });
  await expect(publicado).toContainText("Huaraz, Áncash");
  await expect(publicado).toContainText(`Publicado por ${entidad}`);
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
  ["un viaje", "./?origen=lima&mes=7&dias=6#/ruta/1"],
  ["la zona de un viaje", "./#/polo/33"],
  ["el calendario", "./#/calendario"],
  ["cómo funciona", "./#/acerca"],
  ["guardados", "./#/mis-viajes"],
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
    if (nombre === "un viaje" || nombre === "publicar un evento") {
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
