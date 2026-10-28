import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { POLO } from "../pruebas/api";
import { ClimaAnual } from "./ClimaAnual";

describe("el clima de un polo, mes a mes", () => {
  it("abre en el mes pedido y deja elegir otro para leer su explicación", async () => {
    render(<ClimaAnual clima={POLO.clima} inicial={7} />);
    const meses = screen.getAllByRole("radio");
    expect(meses).toHaveLength(12);
    expect(screen.getByRole("radio", { name: /^Julio: 120 mm de lluvia, buen mes$/ })).toHaveProperty(
      "checked",
      true,
    );
    expect(screen.getByText("Explicación del mes 7.")).toBeDefined();

    await userEvent.click(screen.getByRole("radio", { name: /^Enero/ }));
    expect(screen.getByText("Explicación del mes 1.")).toBeDefined();
    expect(screen.queryByText("Explicación del mes 7.")).toBeNull();
  });

  it("dice lo mismo en una tabla, con el veredicto en palabras", () => {
    render(<ClimaAnual clima={POLO.clima} inicial={7} />);
    const filas = within(screen.getByRole("table", { hidden: true })).getAllByRole("row", { hidden: true });
    expect(filas).toHaveLength(13);
    expect(filas[1]?.textContent).toBe("Enero240 mm——Desaconsejado");
    expect(filas[12]?.textContent).toBe("Diciembre20 mm——Buen mes");
  });
});
