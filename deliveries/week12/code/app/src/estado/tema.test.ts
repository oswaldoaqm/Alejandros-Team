import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CLAVE_TEMA, CLAVE_VIEJA, obtenerTemaInicial, useTema } from "./tema";

/** Un sistema en claro u oscuro, que puede cambiar con la app abierta. */
function sistema(oscuro: boolean) {
  const oyentes = new Set<() => void>();
  const consulta = {
    matches: oscuro,
    media: "(prefers-color-scheme: dark)",
    addEventListener: (_: string, f: () => void) => oyentes.add(f),
    removeEventListener: (_: string, f: () => void) => oyentes.delete(f),
  };
  vi.stubGlobal("matchMedia", () => consulta);
  return (ahora: boolean) => {
    consulta.matches = ahora;
    for (const f of oyentes) f();
  };
}

describe("el tema", () => {
  it("si la persona no eligió, sigue al del sistema", () => {
    sistema(true);
    expect(obtenerTemaInicial()).toBe("dark");
    sistema(false);
    expect(obtenerTemaInicial()).toBe("light");
  });

  it("lo que la persona eligió manda sobre el sistema", () => {
    sistema(true);
    localStorage.setItem(CLAVE_TEMA, "light");
    expect(obtenerTemaInicial()).toBe("light");
  });

  it("de la versión anterior vale el oscuro, que salía del botón, y no el claro, que se guardaba solo", () => {
    sistema(true);
    localStorage.setItem(CLAVE_VIEJA, "light");
    expect(obtenerTemaInicial()).toBe("dark");
    sistema(false);
    localStorage.setItem(CLAVE_VIEJA, "dark");
    expect(obtenerTemaInicial()).toBe("dark");
  });

  it("al abrir no guarda nada; al usar el botón guarda lo elegido y borra la clave vieja", () => {
    sistema(false);
    localStorage.setItem(CLAVE_VIEJA, "light");
    const { result } = renderHook(() => useTema());
    expect(result.current[0]).toBe("light");
    expect(localStorage.getItem(CLAVE_TEMA)).toBeNull();
    act(() => result.current[1]());
    expect(result.current[0]).toBe("dark");
    expect(document.documentElement.getAttribute("data-tema")).toBe("dark");
    expect(localStorage.getItem(CLAVE_TEMA)).toBe("dark");
    expect(localStorage.getItem(CLAVE_VIEJA)).toBeNull();
  });

  it("si el sistema cambia con la app abierta, cambia con él, salvo que la persona haya elegido", () => {
    const cambiar = sistema(false);
    const { result } = renderHook(() => useTema());
    act(() => cambiar(true));
    expect(result.current[0]).toBe("dark");
    act(() => result.current[1]()); // elige claro
    act(() => cambiar(true));
    expect(result.current[0]).toBe("light");
  });
});
