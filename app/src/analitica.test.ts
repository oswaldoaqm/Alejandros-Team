import { beforeEach, describe, expect, it, vi } from "vitest";
import { permitirEstadisticas, registrarEvento } from "./analitica";

beforeEach(() => {
  permitirEstadisticas(false);
  sessionStorage.clear();
  let contador = 0;
  vi.stubGlobal("crypto", {
    randomUUID: () => `11223344-5566-4788-99aa-bbccddeeff${String(contador++).padStart(2, "0")}`,
  });
});

describe("estadísticas opcionales", () => {
  it("no envía ni crea sesión mientras el permiso está apagado", () => {
    const enviar = vi.fn();
    vi.stubGlobal("fetch", enviar);
    registrarEvento("busqueda_iniciada", { origen: "lima", dias: 4 });
    expect(enviar).not.toHaveBeenCalled();
    expect(sessionStorage.length).toBe(0);
  });

  it("envía solo campos estructurados y deja de enviar al revocar", () => {
    const enviar = vi.fn().mockResolvedValue(new Response(null, { status: 202 }));
    vi.stubGlobal("fetch", enviar);
    expect(permitirEstadisticas(true)).toBe(true);
    registrarEvento("busqueda_iniciada", { origen: "lima", dias: 4, intereses: ["naturaleza"] });
    expect(enviar).toHaveBeenCalledTimes(2); // inicio de sesión y búsqueda
    const cuerpo = JSON.parse(enviar.mock.calls[1]?.[1]?.body as string);
    expect(cuerpo).toEqual({
      id_evento: "11223344-5566-4788-99aa-bbccddeeff01",
      sesion: "11223344-5566-4788-99aa-bbccddeeff00",
      tipo: "busqueda_iniciada",
      origen: "lima",
      dias: 4,
      intereses: ["naturaleza"],
    });
    expect(permitirEstadisticas(false)).toBe(true);
    registrarEvento("viaje_guardado", { polo: 12 });
    expect(enviar).toHaveBeenCalledTimes(2);
    expect(sessionStorage.length).toBe(0);
  });

  it("un fallo de analítica no lanza un error al viajero", async () => {
    const enviar = vi.fn().mockRejectedValue(new Error("sin red"));
    vi.stubGlobal("fetch", enviar);
    expect(permitirEstadisticas(true)).toBe(true);
    expect(() => registrarEvento("formulario_abierto")).not.toThrow();
    await Promise.resolve();
    expect(enviar).toHaveBeenCalled();
    permitirEstadisticas(false);
  });
});
