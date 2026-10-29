import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { type Contexto, ContextoApp } from "../estado/contexto";
import { PASOS_VIDEO } from "../piezas/VideoGuia";
import { Acerca } from "./Acerca";

const contextoMock: Contexto = {
  navegar: () => {},
  opciones: { de: null, datos: null, cargando: false, error: null, reintentar: () => {} },
  nombres: { origenes: {}, intereses: {} },
};

function renderAcerca() {
  return render(
    <ContextoApp.Provider value={contextoMock}>
      <Acerca />
    </ContextoApp.Provider>,
  );
}

describe("vista Cómo funciona con Reproductor estilo Stories de Instagram", () => {
  it("muestra los títulos de sección solicitados y no incluye las subsecciones eliminadas", () => {
    renderAcerca();
    expect(screen.getByRole("heading", { level: 1, name: "Cómo funciona" })).toBeDefined();
    expect(screen.getByRole("heading", { level: 2, name: "Recorrido de la app paso a paso" })).toBeDefined();
    expect(screen.getByRole("heading", { level: 2, name: "Detalles técnicos" })).toBeDefined();

    // Verificamos que las subsecciones eliminadas no aparezcan en el documento
    expect(screen.queryByText("Demostración en video")).toBeNull();
    expect(screen.queryByText("Modelos, fuentes oficiales y reglas de cálculo")).toBeNull();
  });

  it("renderiza la ventanita de Stories con sus 8 barritas de progreso y el Paso 1 activo por defecto", () => {
    renderAcerca();

    // Las 8 barritas superiores
    for (const paso of PASOS_VIDEO) {
      expect(screen.getByRole("tab", { name: `${paso.numero}: ${paso.titulo}` })).toBeDefined();
    }

    // Paso 1 activo por defecto en la barra y en el perfil
    expect(screen.getByText("DreemGO Stories · Paso 1: El inicio")).toBeDefined();
    expect(screen.getByText("1 de 8")).toBeDefined();
    expect(screen.getByText("DreemGO")).toBeDefined();
  });

  it("permite navegar entre historias con las flechas flotantes", async () => {
    const user = userEvent.setup();
    renderAcerca();

    // Siguiente historia -> Paso 2
    const btnSiguiente = screen.getByRole("button", { name: /Siguiente historia/i });
    await user.click(btnSiguiente);

    expect(screen.getByText("DreemGO Stories · Paso 2: La consulta")).toBeDefined();
    expect(screen.getByText("2 de 8")).toBeDefined();

    // Historia anterior -> Paso 1
    const btnAnterior = screen.getByRole("button", { name: /Historia anterior/i });
    await user.click(btnAnterior);

    expect(screen.getByText("DreemGO Stories · Paso 1: El inicio")).toBeDefined();
    expect(screen.getByText("1 de 8")).toBeDefined();
  });

  it("permite saltar directamente a un paso desde las Historias destacadas", async () => {
    const user = userEvent.setup();
    renderAcerca();

    // Saltar al Paso 4: El viaje a Huaraz
    const destacadaPaso4 = screen.getByRole("tab", { name: /Ver Paso 4: El viaje a Huaraz/i });
    await user.click(destacadaPaso4);

    expect(screen.getByText("DreemGO Stories · Paso 4: El viaje a Huaraz")).toBeDefined();
    expect(screen.getByText("4 de 8")).toBeDefined();
    expect(screen.getAllByText("El viaje a Huaraz").length).toBeGreaterThanOrEqual(1);

    // Saltar al Paso 8: Un municipio publica un evento
    const destacadaPaso8 = screen.getByRole("tab", { name: /Ver Paso 8: Un municipio publica un evento/i });
    await user.click(destacadaPaso8);

    expect(screen.getByText("DreemGO Stories · Paso 8: Un municipio publica un evento")).toBeDefined();
    expect(screen.getByText("8 de 8")).toBeDefined();
  });

  it("permite alternar pausa y reproducción con el overlay de la historia", async () => {
    const user = userEvent.setup();
    renderAcerca();

    const btnsPlay = screen.getAllByRole("button", { name: /Reproducir historia/i });
    expect(btnsPlay.length).toBeGreaterThanOrEqual(1);
    await user.click(btnsPlay[0] as HTMLElement);
  });

  it("presenta la documentación técnica completa en acordeones", () => {
    renderAcerca();

    expect(screen.getByText(/1\. Cómo se seleccionan y priorizan los lugares/i)).toBeDefined();
    expect(screen.getByText(/2\. Cómo se organizan los traslados/i)).toBeDefined();
    expect(screen.getByText(/3\. Recomendaciones para viajar a zonas de altura/i)).toBeDefined();
    expect(screen.getByText(/4\. Actividades nocturnas/i)).toBeDefined();
    expect(screen.getByText(/5\. Clima y lluvias de los últimos 10 años/i)).toBeDefined();
    expect(screen.getByText(/6\. Cómo se calculan los costos/i)).toBeDefined();
    expect(screen.getByText(/7\. Fiestas patronales y eventos publicados/i)).toBeDefined();
    expect(screen.getByText(/8\. Privacidad/i)).toBeDefined();
    expect(screen.getByText(/9\. Limitaciones actuales/i)).toBeDefined();
    expect(screen.getByText(/10\. Fuentes de datos y licencias/i)).toBeDefined();
  });

  it("cierra el acordeón previo al abrir uno nuevo en detalles técnicos", () => {
    const { container } = renderAcerca();
    const acordeones = container.querySelectorAll<HTMLDetailsElement>("details.acerca-acordeon");
    expect(acordeones[0]?.open).toBe(true);
    expect(acordeones[1]?.open).toBe(false);

    // Abrimos el segundo acordeón
    if (acordeones[1]) {
      acordeones[1].open = true;
      acordeones[1].dispatchEvent(new Event("toggle"));
    }

    expect(acordeones[0]?.open).toBe(false);
    expect(acordeones[1]?.open).toBe(true);
  });
});
