import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorApi, pedir } from "../api/cliente";
import { BuzonComentarios } from "./BuzonComentarios";

vi.mock("../api/cliente", async (original) => ({
  ...(await original<typeof import("../api/cliente")>()),
  pedir: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("buzón del equipo", () => {
  it("solo pide mensajes tras escribir la clave; la envía en cabecera y permite cerrar", async () => {
    vi.mocked(pedir).mockResolvedValue({
      total: 1,
      comentarios: [
        {
          id: "1",
          categoria: "sugerencia",
          mensaje: "Agregar indicaciones de acceso al mirador.",
          instante: "2026-11-11T16:00:00Z",
        },
      ],
    });
    const usuario = userEvent.setup();
    render(<BuzonComentarios />);
    expect(pedir).not.toHaveBeenCalled();
    await usuario.type(screen.getByLabelText("Clave de lectura del equipo"), " clave-de-prueba ");
    await usuario.click(screen.getByRole("button", { name: "Ver mensajes" }));
    await screen.findByText("Agregar indicaciones de acceso al mirador.");
    expect(screen.getByText("1 mensaje recibido")).toBeTruthy();
    expect(vi.mocked(pedir).mock.calls[0]).toEqual([
      "/v1/comentarios",
      { cabeceras: { "X-Clave-Comentarios": "clave-de-prueba" } },
    ]);
    expect(window.location.href).not.toContain("clave-de-prueba");
    await usuario.click(screen.getByRole("button", { name: "Cerrar buzón" }));
    expect(screen.queryByText("Agregar indicaciones de acceso al mirador.")).toBeNull();
    expect((screen.getByLabelText("Clave de lectura del equipo") as HTMLInputElement).value).toBe("");
  });

  it("muestra el estado vacío y permite actualizar con la misma clave mientras está abierto", async () => {
    vi.mocked(pedir).mockResolvedValue({ total: 0, comentarios: [] });
    const usuario = userEvent.setup();
    render(<BuzonComentarios />);
    await usuario.type(screen.getByLabelText("Clave de lectura del equipo"), "clave");
    await usuario.click(screen.getByRole("button", { name: "Ver mensajes" }));
    await screen.findByText("Todavía no hay mensajes. El formulario de ayuda está listo para recibirlos.");
    await usuario.click(screen.getByRole("button", { name: "Actualizar" }));
    await waitFor(() => expect(pedir).toHaveBeenCalledTimes(2));
    expect(vi.mocked(pedir).mock.calls[1]?.[1]?.cabeceras).toEqual({ "X-Clave-Comentarios": "clave" });
  });

  it("rechaza una clave incorrecta sin dejar mensajes visibles", async () => {
    vi.mocked(pedir).mockRejectedValue(new ErrorApi("sin_permiso", "Incorrecta", [], 401));
    const usuario = userEvent.setup();
    render(<BuzonComentarios />);
    await usuario.type(screen.getByLabelText("Clave de lectura del equipo"), "incorrecta");
    await usuario.click(screen.getByRole("button", { name: "Ver mensajes" }));
    expect((await screen.findByRole("alert")).textContent).toContain("no es correcta");
    expect((screen.getByLabelText("Clave de lectura del equipo") as HTMLInputElement).value).toBe("");
    expect(screen.queryByRole("button", { name: "Cerrar buzón" })).toBeNull();
  });

  it("explica cuando el servidor no tiene habilitada la lectura", async () => {
    vi.mocked(pedir).mockRejectedValue(new ErrorApi("sin_permiso", "No configurado", [], 403));
    const usuario = userEvent.setup();
    render(<BuzonComentarios />);
    await usuario.type(screen.getByLabelText("Clave de lectura del equipo"), "clave");
    await usuario.click(screen.getByRole("button", { name: "Ver mensajes" }));
    expect((await screen.findByRole("alert")).textContent).toContain("no tiene habilitada");
  });
});
