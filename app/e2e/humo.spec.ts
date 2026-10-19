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

/** Abre una fila del formulario («Desde», «Cuándo»…) y la cierra con «Listo» si la hoja lo pide. */
async function elegir(pagina: Page, fila: RegExp, accion: () => Promise<void>, listo = true) {
  await pagina.getByRole("button", { name: fila }).click();
  await accion();
  if (listo) await pagina.getByRole("dialog").getByRole("button", { name: "Listo" }).click();
}

test("de la consulta al viaje, con su mapa, sus días y la ficha de cada lugar", async ({ page }) => {
  await page.goto("./");
  await elegir(page, /^Qué te gusta/, () =>
    page.getByRole("checkbox", { name: "Historia y arqueología" }).check(),
  );
  await elegir(page, /^Cuándo/, () => page.getByRole("radio", { name: "Julio" }).check({ force: true }));
  await page.getByRole("button", { name: "Ver mis viajes" }).click();

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

test("desde Lima con seis días al Cusco se vuela, y con «Solo por tierra» no vuela ninguno", async ({
  page,
}) => {
  await page.goto("./?origen=lima&mes=7&dias=6");
  await expect(tarjetas(page)).toHaveCount(3);
  const cusco = tarjetas(page).filter({ hasText: "Cuzco" });
  await expect(cusco).toContainText("con vuelo");
  await cusco.click();
  await expect(page.getByText("desde Lima, con vuelo")).toBeVisible();
  await expect(page.getByRole("region", { name: "Cuánto cuesta" })).toContainText("Vuelos");

  await page.goto("./?origen=lima&mes=7&dias=6&solo_por_tierra=true");
  await expect(tarjetas(page)).toHaveCount(3);
  await expect(tarjetas(page).filter({ hasText: /con (dos )?vuelos?/ })).toHaveCount(0);
});

test("«A dónde»: si el viaje a la zona elegida no cabe, dice qué cambiar, y con eso sale", async ({
  page,
}) => {
  await page.goto("./");
  await elegir(page, /^Cuándo/, () => page.getByRole("radio", { name: "Julio" }).check({ force: true }));
  await elegir(
    page,
    /^A dónde/,
    async () => {
      await page.getByRole("searchbox", { name: "Buscar una zona o un lugar" }).fill("machu picchu");
      await page
        .getByRole("dialog")
        .getByRole("button", { name: /^Machupicchu Pueblo/ })
        .click();
    },
    false,
  );
  await expect(page.getByRole("button", { name: /^A dónde/ })).toContainText("Machupicchu Pueblo");
  await expect(page.getByRole("button", { name: /Sorpréndeme/ })).toHaveCount(0);
  for (let dias = 6; dias > 2; dias--) await page.getByRole("button", { name: "Un día menos" }).click();
  await page.getByRole("button", { name: "Ver mi viaje" }).click();

  await expect(page.getByRole("heading", { level: 2, name: "Así no cabe" })).toBeVisible();
  await expect(
    page.getByText(/^En 2.días no da para ir de Lima a Machupicchu Pueblo y volver/),
  ).toBeVisible();
  await page.getByRole("link", { name: /^Probar con 4.días$/ }).click();
  await expect(titulo(page)).toHaveText("Machupicchu Pueblo");
  await expect(page).toHaveURL(/\?origen=lima&destino=4&mes=7&dias=4&v=[^#]+#\/ruta\/1$/);

  await page.getByRole("link", { name: "Cambiar el viaje" }).click();
  await expect(page.getByRole("button", { name: /^A dónde/ })).toContainText("Machupicchu Pueblo");
});

test("a Huaraz en bus de noche: los tres días son allá, y cada uno con su almuerzo", async ({ page }) => {
  await page.goto("./?origen=lima&destino=14&mes=7&dias=3#/ruta/1");
  await expect(titulo(page)).toHaveText("Huaraz");
  await expect(page.getByText("desde Lima, en bus de noche")).toBeVisible();
  await expect(page.getByRole("region", { name: "Antes de ir" })).toContainText(
    /sales de Lima a las \d\d:\d\d la noche antes del día 1 y vuelves la noche del día 3/,
  );
  const dias = page.locator(".dia-fila");
  await expect(dias).toHaveCount(3);
  await expect(dias.nth(0)).toContainText("Ida y visitas");
  await expect(dias.nth(2)).toContainText("Visitas y vuelta");

  await page.getByRole("radio", { name: "Día 1" }).check({ force: true });
  // En la página va también el plan para imprimir, que no se ve: se busca en el día.
  const elDia = page.locator(".un-dia");
  await expect(
    elDia.getByText(/^El bus de noche sale de Lima a las \d\d:\d\d de la noche anterior/),
  ).toBeVisible();
  const almuerzo = page.locator(".lugares__almuerzo");
  await expect(almuerzo).toHaveCount(1);
  await expect(almuerzo).toContainText(/^\d\d:\d\d Almuerzo/);
  // La hora del almuerzo no es un lugar: no se abre.
  await expect(almuerzo.getByRole("button")).toHaveCount(0);

  await page.getByRole("radio", { name: "Día 3" }).check({ force: true });
  await expect(elDia.getByText(/^En la noche, el bus de vuelta: sale de Huaraz a las/)).toBeVisible();
  const informe = await new AxeBuilder({ page }).withTags(PAUTAS).include(".un-dia").analyze();
  expect(informe.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length})`)).toEqual([]);
});

test("guardar un viaje lo deja en «Guardados» de este navegador, y de ahí se vuelve a él", async ({
  page,
}) => {
  await page.goto("./?origen=lima&mes=7&dias=3#/ruta/2");
  await expect(page.getByRole("link", { name: "Tus viajes" })).toBeVisible();
  const nombre = await titulo(page).innerText();
  // Exacto: «Imprimir o guardar en PDF» también dice «guardar».
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Guardado", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("link", { name: "Guardados" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Guardados" })).toBeFocused();
  // El guardado lleva el nombre del viaje y, debajo, lo que se pidió.
  await page.getByRole("link", { name: /Desde Lima, 3.días en julio/ }).click();
  await expect(page.getByRole("link", { name: "Tus viajes" })).toBeVisible();
  await expect(titulo(page)).toHaveText(nombre);
  await expect(page).toHaveURL(/#\/ruta\/2$/);
});

test("con «Vida nocturna», cada noche en la zona trae dónde salir, y la primera en la altura, descanso", async ({
  page,
}) => {
  await page.goto("./?origen=lima&mes=7&dias=6&intereses=vida_nocturna#/ruta/1");
  await expect(titulo(page)).toHaveText("Cuzco");
  const dias = page.locator(".dia-fila");
  await expect(dias.nth(0)).toContainText("De noche: Noche tranquila");
  await expect(dias.nth(1)).toContainText("De noche: Salir en Cuzco");
  await expect(dias.nth(5)).not.toContainText("De noche"); // el día en que se vuelve no se duerme allá

  const lugaresDe = async (dia: number) => {
    await page.getByRole("radio", { name: `Día ${dia}` }).check({ force: true });
    const noche = page.getByRole("region", { name: "De noche: Salir en Cuzco" });
    const enlaces = noche.getByRole("list", { name: "Para esta noche" }).getByRole("link");
    await expect(enlaces).toHaveCount(3);
    await expect(enlaces.first()).toHaveAttribute("href", /^https:\/\/www\.openstreetmap\.org\//);
    return enlaces.allInnerTexts();
  };
  const delDos = await lugaresDe(2);
  const delTres = await lugaresDe(3);
  expect(
    delTres.filter((n) => delDos.includes(n)),
    "otra noche, otros lugares",
  ).toEqual([]);
});

test("una noche de estrellas, con fecha: la luna de esa noche y el cielo de la zona mes a mes", async ({
  page,
}) => {
  await page.goto(
    "./?origen=lima&fecha_inicio=2027-07-03&dias=6&intereses=naturaleza&intereses=vida_nocturna&destino=36#/ruta/1",
  );
  await page.getByRole("radio", { name: "Día 2" }).check({ force: true });
  const estrellas = page.getByRole("region", { name: /^De noche: Estrellas en / });
  await expect(estrellas).toContainText(/Luna al \d+.%/);
  await expect(estrellas).toContainText("Cielo con luz");
  await expect(estrellas).toContainText(/oscurece del todo a las \d\d:\d\d/);

  await page.getByRole("link", { name: /^Ver todos los lugares de la zona/ }).click();
  const zona = page.getByRole("region", { name: "De noche" });
  await expect(zona.getByRole("heading", { name: "Para salir" })).toBeVisible();
  await expect(zona.getByRole("heading", { name: "Para ver estrellas" })).toBeVisible();
  await expect(zona.locator(".despejadas__mes")).toHaveCount(12);
  await expect(zona.locator(".despejadas__mes--elegido")).toContainText(
    /^Julio: \d+ de cada 10 noches despejadas/,
  );
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
  await expect(page.getByText(/sale también en los viajes que pasan a 10 km o menos/)).toBeVisible();
  await expect(page.locator(".evento")).toContainText(`Publicado por ${entidad}`);

  // Y está en el calendario de su mes, que se pide de nuevo al API. Un mes puede traer más de
  // treinta fiestas, y las que pasan de treinta esperan a «Ver N eventos más»: con su región se ve.
  await page.getByRole("link", { name: /^Ver el calendario de / }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Fiestas" })).toBeVisible();
  await page.getByLabel("Región").selectOption("Áncash");
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

const PAUTAS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

const PANTALLAS = [
  ["el formulario", "./"],
  ["los resultados", "./?origen=lima&mes=7&dias=6&intereses=historia&presupuesto=1500&altitud_max=3800"],
  ["un viaje", "./?origen=lima&mes=7&dias=6#/ruta/1"],
  ["un viaje a una zona que no cabe", "./?origen=lima&destino=4&mes=7&dias=2#/ruta/1"],
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
      .withTags(PAUTAS)
      .exclude(".maplibregl-canvas-container")
      .exclude(".maplibregl-control-container")
      .analyze();
    expect(informe.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length})`)).toEqual([]);
  });
}

test("cada tipo de noche: sin fallas de accesibilidad que una máquina detecte", async ({ page }) => {
  await page.goto(
    "./?origen=lima&fecha_inicio=2027-07-03&dias=6&intereses=naturaleza&intereses=vida_nocturna&destino=36#/ruta/1",
  );
  // Descanso, estrellas y salir: el fondo de noche es lo único oscuro en el tema claro.
  for (const [dia, tipo] of [
    [1, "descanso"],
    [2, "estrellas"],
    [3, "salir"],
  ] as const) {
    await page.getByRole("radio", { name: `Día ${dia}` }).check({ force: true });
    await expect(page.locator(`.noche--${tipo}`)).toBeVisible();
    const informe = await new AxeBuilder({ page }).withTags(PAUTAS).include(".noche").analyze();
    expect(informe.violations.map((v) => `${tipo}: ${v.id} (${v.nodes.length})`)).toEqual([]);
  }
});
