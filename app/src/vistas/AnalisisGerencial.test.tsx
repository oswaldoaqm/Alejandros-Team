import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { type Analisis, AnalisisGerencial, type VistaGerencial } from "./AnalisisGerencial";

const datos: Analisis = {
  distribucion: [
    { id: "solo_inicio", nombre: "Solo inicio", cantidad: 8, porcentaje: 80 },
    { id: "guardado", nombre: "Con guardado", cantidad: 2, porcentaje: 20 },
  ],
  embudo: [
    { id: "inicio", nombre: "Inicio", sesiones: 10, porcentaje: 100 },
    { id: "guardado", nombre: "Guardado", sesiones: 2, porcentaje: 20 },
  ],
  pareto: [{ nombre: "Solo inicio", cantidad: 8, porcentaje: 100, acumulado: 100 }],
  mapa_calor: [{ dia: 0, hora: 10, acciones: 12 }],
  latencia: {
    n: 3,
    media: 500,
    mediana: 400,
    p25: 250,
    p75: 700,
    p95: 900,
    desviacion: 300,
    minimo: 100,
    maximo: 1000,
    histograma: [
      { desde: 0, hasta: 500, cantidad: 2 },
      { desde: 500, hasta: 1000, cantidad: 1 },
    ],
  },
  correlacion: {
    variables: [
      { id: "dias", nombre: "Días" },
      { id: "presupuesto", nombre: "Presupuesto" },
    ],
    pares: [
      { x: "dias", y: "dias", r: 1, n: 10 },
      { x: "dias", y: "presupuesto", r: null, n: 3 },
      { x: "presupuesto", y: "dias", r: null, n: 3 },
      { x: "presupuesto", y: "presupuesto", r: null, n: 3 },
    ],
    nota: "Se usan pares completos. No se estima con menos de cinco pares.",
  },
  dispersion: [
    { dias: 3, presupuesto: 700 },
    { dias: 3, presupuesto: 700 },
  ],
  proyeccion: {
    estado: "disponible",
    metodo: "Promedio de los últimos 7 días",
    dias_historia: 28,
    n_validacion: 7,
    mae_validacion: 2.5,
    candidatos: [
      { metodo: "Promedio de los últimos 7 días", mae: 2.5 },
      { metodo: "Tendencia lineal", mae: 3.1 },
    ],
    historico: [
      { fecha: "2026-11-09", valor: 8 },
      { fecha: "2026-11-10", valor: 7 },
    ],
    futuro: [{ fecha: "2026-11-11", valor: 7.2 }],
    nota: "Validación temporal con los siete días finales. No es una garantía de demanda.",
  },
  nota: "Datos simulados para aprender.",
};
const serie = [{ fecha: "2026-11-10", sesiones: 10, busquedas: 8, detalles: 4, guardados: 2 }];

function mostrar(vista: VistaGerencial, analisis = datos) {
  render(<AnalisisGerencial datos={analisis} vista={vista} serie={serie} indicadores={[]} simulacion />);
}

describe("vistas gerenciales", () => {
  it("separa resumen y estadística para evitar mezclar todas las gráficas", () => {
    mostrar("resumen");
    expect(
      screen.getByRole("img", { name: "Gráfico combinado de sesiones y búsquedas por día" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("img", { name: "Distribución circular de sesiones por estado alcanzado" }),
    ).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Matriz de correlación de Pearson" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Con guardado/ }));
    expect(screen.getByRole("button", { name: /Con guardado/ }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText("seleccionadas")).toBeTruthy();
  });

  it("permite consultar la celda del mapa de calor sin atribuir causas", () => {
    mostrar("comportamiento");
    fireEvent.click(screen.getByRole("button", { name: "Lunes, 10:00, 12 acciones" }));
    expect(screen.getByRole("status").textContent).toContain("12 acciones");
    expect(screen.getByText("NO SON CAUSAS DEMOSTRADAS")).toBeTruthy();
    expect(screen.getByRole("img", { name: "Pareto de estados de sesiones sin guardar" })).toBeTruthy();
    expect(screen.getByText(/80 % es una referencia visual/)).toBeTruthy();
  });

  it("muestra correlaciones ausentes como ausentes y conserva el número de pares", () => {
    mostrar("estadistica");
    const celda = screen.getByRole("button", { name: "Días y Presupuesto: sin datos suficientes, n 3" });
    expect(celda.textContent).toContain("—");
    fireEvent.click(celda);
    expect(screen.getByRole("status").textContent).toContain("no se puede estimar");
    expect(screen.getByRole("status").textContent).toContain("3 pares completos");
    expect(screen.getByText(/Una correlación no demuestra causa y efecto/)).toBeTruthy();
    expect(screen.getByRole("img", { name: /Dispersión de días solicitados/ })).toBeTruthy();
  });

  it("distingue la proyección didáctica de la actividad observada y muestra su error", () => {
    mostrar("proyeccion");
    expect(screen.getByText("EJERCICIO CON DATOS SIMULADOS")).toBeTruthy();
    expect(screen.getAllByText("2.5 sesiones/día")).toHaveLength(2);
    expect(
      screen.getByRole("img", { name: "Historia y proyección de sesiones para los próximos siete días" }),
    ).toBeTruthy();
    expect(screen.queryByRole("img", { name: /Distribución circular/ })).toBeNull();
  });

  it("no dibuja una predicción cuando el historial es insuficiente", () => {
    mostrar("proyeccion", {
      ...datos,
      proyeccion: {
        ...datos.proyeccion,
        estado: "insuficiente",
        dias_historia: 3,
        futuro: [],
        metodo: null,
        mae_validacion: null,
        candidatos: [],
      },
    });
    expect(screen.getByText(/Hay 3 días disponibles/)).toBeTruthy();
    expect(screen.queryByRole("img", { name: /Historia y proyección/ })).toBeNull();
  });

  it("resuelve el periodo vacío sin mostrar un círculo con proporciones inventadas", () => {
    mostrar("resumen", { ...datos, distribucion: [] });
    expect(screen.getByText("Aún no hay sesiones en el periodo.")).toBeTruthy();
    expect(screen.queryByRole("img", { name: /Distribución circular/ })).toBeNull();
  });

  it("actualiza la celda de calor seleccionada cuando cambia el periodo", () => {
    const { rerender } = render(
      <AnalisisGerencial datos={datos} vista="comportamiento" serie={serie} indicadores={[]} simulacion />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Lunes, 10:00, 12 acciones" }));
    rerender(
      <AnalisisGerencial
        datos={{ ...datos, mapa_calor: [{ dia: 0, hora: 10, acciones: 2 }] }}
        vista="comportamiento"
        serie={serie}
        indicadores={[]}
        simulacion
      />,
    );
    expect(screen.getByRole("status").textContent).toContain("2 acciones");
    expect(screen.getByRole("status").textContent).not.toContain("12 acciones");
  });

  it("actualiza el coeficiente y su muestra seleccionados después de una nueva lectura", () => {
    const { rerender } = render(
      <AnalisisGerencial datos={datos} vista="estadistica" serie={serie} indicadores={[]} simulacion />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Días y Presupuesto: sin datos suficientes, n 3" }));
    const actualizado = {
      ...datos,
      correlacion: {
        ...datos.correlacion,
        pares: datos.correlacion.pares.map((p) =>
          p.x === "dias" && p.y === "presupuesto" ? { ...p, r: 0.7, n: 20 } : p,
        ),
      },
    };
    rerender(
      <AnalisisGerencial datos={actualizado} vista="estadistica" serie={serie} indicadores={[]} simulacion />,
    );
    expect(screen.getByRole("status").textContent).toContain("r = 0.7");
    expect(screen.getByRole("status").textContent).toContain("20 pares completos");
  });
});
