import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Cargando } from "./Estados";

describe("la espera", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("al principio solo dice qué está haciendo", () => {
    render(<Cargando texto="Preparando el planificador…" />);
    expect(screen.getByRole("status").textContent).toBe("Preparando el planificador…");
  });

  it("si tarda, avisa que el servidor puede estar despertando", () => {
    render(<Cargando texto="Preparando el planificador…" />);
    act(() => {
      vi.advanceTimersByTime(8_000);
    });
    expect(screen.getByRole("status").textContent).toContain("hasta un minuto en despertar");
  });
});
