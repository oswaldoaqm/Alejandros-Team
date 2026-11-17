import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ErrorApi, pedir } from "../api/cliente";
import { Indicadores } from "./Indicadores";

vi.mock("../api/cliente", async (original) => ({
  ...(await original<typeof import("../api/cliente")>()),
  pedir: vi.fn(),
}));

const resumen = {
  modo: "simulacion",
  actualizado: "2026-11-11T12:00:00Z",
  consultado: "2026-11-11T12:01:00Z",
  total_eventos: 900,
  actividad_reciente: [
    { instante: "2026-11-11T12:00:00Z", tipo: "busqueda_iniciada", etiqueta: "Búsqueda iniciada" },
  ],
  periodo: { desde: null, hasta: null },
  indicadores: Array.from({ length: 22 }, (_, i) => ({
    id: `indicador_${i}`,
    etiqueta: `Indicador ${i + 1}`,
    valor: i + 1,
    descripcion: `Qué mide el indicador ${i + 1}`,
    grupo: i < 11 ? "uso" : "calidad",
  })),
  serie: [{ fecha: "2026-11-11", sesiones: 300, busquedas: 220, detalles: 180, guardados: 65 }],
  destinos: [{ nombre: "Puno", cantidad: 40 }],
  intereses: [{ nombre: "Naturaleza", cantidad: 70 }],
  fuente: "SIMULACIÓN: 300 sesiones generadas; no son usuarios ni compras reales.",
};

describe("panel de indicadores", () => {
  it("muestra 22 indicadores y deja clara la simulación", async () => {
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    expect(await screen.findByRole("heading", { name: "22 indicadores" })).toBeTruthy();
    expect(screen.getAllByText(/^Indicador \d+$/)).toHaveLength(22);
    expect(screen.getByText(/200 usuarios ficticios/)).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Destinos más abiertos" })).toBeTruthy();
    expect(screen.getByRole("img", { name: /Búsquedas por día/ })).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Uso" }));
    expect(screen.getByRole("heading", { name: "11 indicadores" })).toBeTruthy();
    expect(screen.getAllByText(/^Indicador \d+$/)).toHaveLength(11);
  });

  it("compara dos series diarias del mismo periodo sin crear nuevos datos", async () => {
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    expect(await screen.findByRole("img", { name: /Búsquedas por día/ })).toBeTruthy();
    await userEvent.selectOptions(screen.getByLabelText("Comparar con"), "guardados");
    expect(screen.getByRole("img", { name: /Búsquedas y Guardados por día/ })).toBeTruthy();
    await userEvent.selectOptions(screen.getByLabelText("Mostrar"), "guardados");
    expect(screen.getByRole("img", { name: /Guardados por día/ })).toBeTruthy();
    expect((screen.getByLabelText("Comparar con") as HTMLSelectElement).value).toBe("ninguna");
  });

  it("pide la clave para datos reales y nunca la agrega a la URL", async () => {
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    await screen.findByRole("heading", { name: "22 indicadores" });
    const llamadasDemo = vi.mocked(pedir).mock.calls.length;
    await userEvent.click(screen.getByRole("button", { name: "Actividad registrada" }));
    expect(screen.queryByRole("heading", { name: "22 indicadores" })).toBeNull();
    expect(screen.getByLabelText("Clave de lectura del panel")).toBeTruthy();
    expect(vi.mocked(pedir).mock.calls.length).toBe(llamadasDemo);
    fireEvent.change(screen.getByLabelText("Clave de lectura del panel"), {
      target: { value: "clave-de-prueba" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Ver actividad" }));
    await waitFor(() => expect(vi.mocked(pedir).mock.calls.length).toBeGreaterThan(llamadasDemo));
    const llamada = vi.mocked(pedir).mock.calls.at(-1);
    expect(llamada?.[0]).toBe("/v1/analitica/resumen");
    expect(llamada?.[1]?.parametros?.get("modo")).toBe("real");
    expect(llamada?.[1]?.parametros?.toString()).not.toContain("clave-de-prueba");
    expect(llamada?.[1]?.cabeceras).toEqual({ "X-Clave-Analitica": "clave-de-prueba" });
  });

  it("actualiza la actividad cada tres segundos y conserva la última lectura si falla la red", async () => {
    vi.useFakeTimers();
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    await act(async () => {
      await Promise.resolve();
    });
    fireEvent.click(screen.getByRole("button", { name: "Actividad registrada" }));
    fireEvent.change(screen.getByLabelText("Clave de lectura del panel"), { target: { value: "clave" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Ver actividad" }));
    });
    const antes = vi.mocked(pedir).mock.calls.length;
    expect(screen.getByText("En vivo · lectura cada 3 segundos")).toBeTruthy();
    vi.mocked(pedir).mockResolvedValue({ ...resumen, modo: "real", total_eventos: 901 });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(vi.mocked(pedir).mock.calls.length).toBe(antes + 1);
    expect(screen.getByText("901 acciones")).toBeTruthy();
    vi.mocked(pedir).mockRejectedValue(new Error("sin conexión"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(screen.getByText("901 acciones")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("última lectura correcta");
  });

  it("permite corregir una clave rechazada sin dejar cifras visibles", async () => {
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    await screen.findByRole("heading", { name: "22 indicadores" });
    await userEvent.click(screen.getByRole("button", { name: "Actividad registrada" }));
    vi.mocked(pedir).mockRejectedValue(new ErrorApi("sin_permiso", "No autorizado", [], 401));
    fireEvent.change(screen.getByLabelText("Clave de lectura del panel"), {
      target: { value: "incorrecta" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Ver actividad" }));
    await screen.findByRole("alert");
    expect(screen.getByLabelText("Clave de lectura del panel")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "22 indicadores" })).toBeNull();
  });

  it("explica cuando el servidor no configuró acceso a actividad real", async () => {
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    await screen.findByRole("heading", { name: "22 indicadores" });
    await userEvent.click(screen.getByRole("button", { name: "Actividad registrada" }));
    vi.mocked(pedir).mockRejectedValue(new ErrorApi("sin_permiso", "Sin configurar", [], 403));
    fireEvent.change(screen.getByLabelText("Clave de lectura del panel"), { target: { value: "clave" } });
    await userEvent.click(screen.getByRole("button", { name: "Ver actividad" }));
    const alerta = await screen.findByRole("alert");
    expect(alerta.textContent).toContain("no tiene habilitada la lectura");
    expect(screen.queryByRole("heading", { name: "22 indicadores" })).toBeNull();
  });

  it("detiene la actualización cuando la pestaña queda oculta", async () => {
    vi.useFakeTimers();
    const estado = vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    vi.mocked(pedir).mockResolvedValue(resumen);
    render(<Indicadores />);
    await act(async () => {
      await Promise.resolve();
    });
    fireEvent.click(screen.getByRole("button", { name: "Actividad registrada" }));
    fireEvent.change(screen.getByLabelText("Clave de lectura del panel"), { target: { value: "clave" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Ver actividad" }));
    });
    estado.mockReturnValue("hidden");
    fireEvent(document, new Event("visibilitychange"));
    const antes = vi.mocked(pedir).mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });
    expect(vi.mocked(pedir).mock.calls.length).toBe(antes);
    estado.mockRestore();
  });
});
