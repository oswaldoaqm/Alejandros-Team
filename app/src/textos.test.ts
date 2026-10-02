import { describe, expect, it } from "vitest";
import { POR_DEFECTO } from "./consulta";
import { plano } from "./pruebas/texto";
import { aplicarSugerencia, conQueSeViaja, entrada, textoDeSugerencia, tipoDeDia } from "./textos";

const NOMBRES = {
  origenes: { cusco: "Cusco" },
  intereses: { playa: "Playa", historia: "Historia y arqueología" },
};
const JULIO = { ...POR_DEFECTO, mes: 7, altitud_max: 3000, intereses: ["playa"] };

describe("el día", () => {
  it("dice qué se hace, y un día de visitas sin paradas es un día libre", () => {
    expect(tipoDeDia({ tipo: "ida_y_visita", paradas: [] })).toBe("Ida y visitas");
    expect(tipoDeDia({ tipo: "ida_visita_y_vuelta" })).toBe("Ida, visitas y vuelta");
    expect(tipoDeDia({ tipo: "visita", paradas: [] })).toBe("Día libre");
    expect(tipoDeDia({ tipo: "vuelta", paradas: [] })).toBe("Vuelta");
  });
});

describe("con qué se viaja", () => {
  it("lo dice con las palabras del motor", () => {
    expect(conQueSeViaja(["carretera"])).toBe("por carretera");
    expect(conQueSeViaja(["carretera", "bote"])).toBe("por carretera y en bote");
    expect(conQueSeViaja(["carretera", "tren", "bote"])).toBe("por carretera, en tren y en bote");
    expect(conQueSeViaja(undefined)).toBe("por carretera");
  });
});

describe("la entrada de un lugar", () => {
  it("dice lo que la ficha publica y nada más", () => {
    expect(entrada({ ingreso: "libre", tarifa_soles: 0 })).toBe("Entrada libre");
    expect(plano(entrada({ ingreso: "pagado", tarifa_soles: 2.5 }))).toBe("Entrada S/ 2,50");
    expect(entrada({ ingreso: "pagado", tarifa_soles: null })).toBe("Entrada pagada, sin tarifa publicada");
    expect(entrada({ ingreso: "desconocido" })).toBe("La ficha no dice si se paga");
  });
});

describe("las sugerencias del motor cuando no hay rutas", () => {
  it("cada una arma la consulta que propone", () => {
    expect(aplicarSugerencia(JULIO, { campo: "dias", valor: 8, efecto: "" })).toMatchObject({
      dias: 8,
      mes: 7,
    });
    expect(
      aplicarSugerencia(JULIO, { campo: "altitud_max", valor: null, efecto: "" })?.altitud_max,
    ).toBeNull();
    expect(aplicarSugerencia(JULIO, { campo: "intereses", valor: [], efecto: "" })?.intereses).toEqual([]);
    expect(aplicarSugerencia(JULIO, { campo: "presupuesto", valor: 900, efecto: "" })?.presupuesto).toBe(900);
    expect(aplicarSugerencia(JULIO, { campo: "origen", valor: "cusco", efecto: "" })?.origen).toBe("cusco");
    expect(
      aplicarSugerencia({ ...JULIO, fecha_inicio: "2027-07-20" }, { campo: "mes", valor: 8, efecto: "" }),
    ).toMatchObject({ mes: 8, fecha_inicio: null });
  });

  it("una sugerencia que no se entiende no se ofrece", () => {
    expect(aplicarSugerencia(JULIO, { campo: "dias", valor: "muchos", efecto: "" })).toBeNull();
    expect(aplicarSugerencia(JULIO, { campo: "origen", valor: 3, efecto: "" })).toBeNull();
  });

  it("se escriben como una acción", () => {
    const texto = (
      campo: Parameters<typeof textoDeSugerencia>[0]["campo"],
      valor: number | string | string[] | null,
    ) => plano(textoDeSugerencia({ campo, valor, efecto: "" }, NOMBRES));
    expect(texto("dias", 8)).toBe("Probar con 8 días");
    expect(texto("altitud_max", null)).toBe("Quitar el límite de altitud");
    expect(texto("altitud_max", 4200)).toBe("Subir el límite de altitud a 4 200 m");
    expect(texto("intereses", [])).toBe("Buscar sin filtrar por intereses");
    expect(texto("intereses", ["playa", "historia"])).toBe("Buscar solo playa y historia y arqueología");
    expect(texto("presupuesto", null)).toBe("Quitar el tope de presupuesto");
    expect(texto("mes", 8)).toBe("Probar en agosto");
    expect(texto("origen", "cusco")).toBe("Salir desde Cusco");
  });
});
