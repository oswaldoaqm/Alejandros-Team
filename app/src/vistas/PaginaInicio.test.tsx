import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { obtenerFestividadesVivas } from "../datos/festividades";
import { irA, ponerApi } from "../pruebas/api";

// Las festividades de la portada dependen del día: estas pruebas van al 3 de noviembre de 2026.
function el3DeNoviembre() {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 3, 12));
}

describe("página de inicio", () => {
  it("muestra el carrusel hero, el CTA a Planear, festividades del mes y el blog viajero", async () => {
    el3DeNoviembre();
    irA("./");
    ponerApi();
    render(<App />);

    // 1. Carrusel Hero
    expect(screen.getByRole("region", { name: "Destinos destacados del Perú" })).toBeDefined();
    expect(screen.getByRole("heading", { level: 2, name: /Camina el Cusco/i })).toBeDefined();

    // 2. Banner de acceso rápido a Planear
    expect(
      screen.getByRole("heading", { level: 2, name: "Tu planificador inteligente de viajes" }),
    ).toBeDefined();
    expect(screen.getByText("¿Qué esperas para explorar?")).toBeDefined();
    const btnPlanear = screen.getByRole("link", { name: /Armar mi viaje/i });
    expect(btnPlanear.getAttribute("href")).toBe("./#/planear");
    const btnComoFunciona = within(btnPlanear.parentElement as HTMLElement).getByRole("link", {
      name: /Cómo funciona/i,
    });
    expect(btnComoFunciona.getAttribute("href")).toBe("./#/acerca");

    // 3. Festividades y eventos del mes (Dinámico según la fecha actual)
    expect(screen.getByRole("heading", { level: 2, name: "Festividades y eventos del mes" })).toBeDefined();
    expect(screen.getByRole("region", { name: "Festividades destacadas del mes" })).toBeDefined();
    const festividadesVivas = obtenerFestividadesVivas();
    for (const fiesta of festividadesVivas) {
      expect(screen.getByText(fiesta.titulo)).toBeDefined();
    }

    const btnTodasFiestas = screen.getByRole("link", { name: /Ver todas las festividades/i });
    expect(btnTodasFiestas.getAttribute("href")).toBe("./#/calendario");

    // 4. Apartado de Blog viajero
    expect(screen.getByRole("heading", { level: 2, name: "Blog viajero" })).toBeDefined();
    expect(screen.getByRole("region", { name: "Notas destacadas del blog viajero" })).toBeDefined();
    expect(
      screen.getByText(/Virgen de la Candelaria 2027: todo sobre su presentación oficial/i),
    ).toBeDefined();
    expect(
      screen.getByText("Viaja a Tarma y vive la fiesta del Valle de las Flores: 7 planes imperdibles"),
    ).toBeDefined();
    expect(
      screen.getByText("¿Qué hacer en Chanchamayo? 8 planes entre cataratas, café y naturaleza"),
    ).toBeDefined();
    expect(
      screen.getByText("Festival Rural Tour Huayllay: vive dos días de naturaleza y tradición en Pasco"),
    ).toBeDefined();

    const btnTodasNotas = screen.getByRole("link", { name: /Ver todas las notas/i });
    expect(btnTodasNotas.getAttribute("href")).toBe("./#/blog");
  });

  it("la cabecera y la barra inferior contienen las mismas 4 secciones: Inicio, Planear, Guardados y Cómo funciona", () => {
    irA("./");
    ponerApi();
    render(<App />);

    const navs = screen.getAllByRole("navigation", { name: "Secciones" });
    expect(navs.length).toBeGreaterThanOrEqual(2);
    const cabeceraNav = navs[0] as HTMLElement;
    const barraInferiorNav = navs[1] as HTMLElement;

    // Ambas barras tienen exactamente las mismas 4 secciones
    for (const barra of [cabeceraNav, barraInferiorNav]) {
      expect(within(barra).getByRole("link", { name: "Inicio" }).getAttribute("href")).toBe("./");
      expect(within(barra).getByRole("link", { name: "Planear" }).getAttribute("href")).toBe("./#/planear");
      expect(within(barra).getByRole("link", { name: "Guardados" }).getAttribute("href")).toBe(
        "./#/mis-viajes",
      );
      expect(within(barra).getByRole("link", { name: "Cómo funciona" }).getAttribute("href")).toBe(
        "./#/acerca",
      );

      // Ni Fiestas ni Blog están en las barras
      expect(within(barra).queryByRole("link", { name: "Fiestas" })).toBeNull();
      expect(within(barra).queryByRole("link", { name: "Blog" })).toBeNull();
    }
  });

  it("permite navegar a Planear desde el banner CTA", async () => {
    irA("./");
    ponerApi();
    render(<App />);

    const btnArmar = screen.getByRole("link", { name: /Armar mi viaje/i });
    await userEvent.click(btnArmar);
    expect(await screen.findByRole("button", { name: /^Desde/ })).toBeDefined();
  });

  it("al presionar «Ver más» en una festividad se abre su hoja de detalle con botón para planear viaje", async () => {
    el3DeNoviembre();
    irA("./");
    ponerApi();
    render(<App />);

    const festividades = obtenerFestividadesVivas();
    const primeraFiesta = festividades[0];
    expect(primeraFiesta).toBeDefined();
    if (!primeraFiesta) {
      throw new Error("No hay festividades activas");
    }
    const botonVerMas = screen.getByRole("button", {
      name: new RegExp(`Ver más sobre ${primeraFiesta.titulo}`, "i"),
    });
    await userEvent.click(botonVerMas);

    const hoja = screen.getByRole("dialog", {
      name: primeraFiesta.titulo,
    });
    expect(hoja).toBeDefined();
    expect(within(hoja).getByText("Actividades destacadas")).toBeDefined();

    const btnPlanear = within(hoja).getByRole("link", {
      name: new RegExp(`Planear viaje a ${primeraFiesta.lugar}`, "i"),
    });
    expect(btnPlanear.getAttribute("href")).toContain("#/planear");

    // Se puede cerrar con el botón de cerrar
    const btnCerrar = within(hoja).getByRole("button", { name: "Cerrar" });
    await userEvent.click(btnCerrar);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("las festividades rotan automáticamente conforme avanza la fecha (ej. el 14 de noviembre)", () => {
    // Al 3 de noviembre (primera quincena activa)
    const fiestasHoy = obtenerFestividadesVivas(new Date("2026-11-03T12:00:00"));
    expect(fiestasHoy.map((f) => f.id)).toEqual([
      "festival-salchicha-huachana",
      "festival-orquidea-moyobamba",
      "escenificacion-quespiwanca-tinkuy",
      "patronal-san-martin-tours-sechura",
    ]);

    // Al 14 de noviembre (los de la primera quincena ya pasaron, entran automáticamente los siguientes)
    const fiestas14Nov = obtenerFestividadesVivas(new Date("2026-11-14T12:00:00"));
    expect(fiestas14Nov.map((f) => f.id)).toEqual([
      "festival-camu-camu-iquitos",
      "festival-apicola-illimo",
      "patronal-virgen-inmaculada-juli",
      "patronal-virgen-de-la-puerta-otuzco",
    ]);
  });
});
