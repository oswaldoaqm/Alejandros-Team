import { describe, expect, it } from "vitest";
import { artefactosDe, cambioDeVersion } from "./version";

describe("la versión de datos", () => {
  it("separa la parte de los artefactos de la huella de lo publicado", () => {
    expect(artefactosDe("2026.10.2")).toBe("2026.10.2");
    expect(artefactosDe("2026.10.2-e3f9a1c0")).toBe("2026.10.2");
    expect(artefactosDe("2026.10.2-beta")).toBe("2026.10.2-beta");
  });

  it("dice si entre el enlace y lo vigente cambiaron los datos o solo los eventos publicados", () => {
    expect(cambioDeVersion(null, "2026.10.2")).toBe("ninguno");
    expect(cambioDeVersion("2026.10.2", "2026.10.2")).toBe("ninguno");
    expect(cambioDeVersion("2026.10.2-e3f9a1c", "2026.10.2-e3f9a1c")).toBe("ninguno");
    expect(cambioDeVersion("2026.10.2", "2026.10.2-e3f9a1c")).toBe("eventos");
    expect(cambioDeVersion("2026.10.2-e3f9a1c", "2026.10.2")).toBe("eventos");
    expect(cambioDeVersion("2026.10.2-e3f9a1c", "2026.10.2-e77b0d2")).toBe("eventos");
    expect(cambioDeVersion("2026.10.1", "2026.10.2")).toBe("datos");
    expect(cambioDeVersion("2026.10.1-e3f9a1c", "2026.10.2-e3f9a1c")).toBe("datos");
  });
});
