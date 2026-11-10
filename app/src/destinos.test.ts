import { describe, expect, it } from "vitest";
import publicada from "../public/destinos.json";
import {
  buscarZonas,
  canonica,
  type Destinos,
  type Encontrada,
  lugarPrincipal,
  nombreDeZona,
  notaDeZona,
  type Zona,
  zonasDestacadas,
} from "./destinos";
import { DESTINOS } from "./pruebas/api";

const ids = (texto: string, destinos: Destinos = DESTINOS) =>
  buscarZonas(destinos, texto).map((e) => e.zona.id);
const zona = (id: number) => DESTINOS.zonas.find((z) => z.id === id) as Zona;

describe("cómo se comparan los nombres", () => {
  it("junta las grafías del quechua y del castellano, como el pipeline", () => {
    expect(canonica("cuzco")).toBe(canonica("cusco"));
    expect(canonica("qorikancha")).toBe(canonica("coricancha"));
    expect(canonica("huaraz")).toBe(canonica("waras"));
    expect(canonica("kuelap")).toBe(canonica("cuelap"));
    expect(canonica("xauxa")).toBe(canonica("jauja"));
    // La h de «ch» se queda, también en «chua».
    expect(canonica("chachapoyas")).toBe("chachapoias");
    expect(canonica("chua")).toBe("chua");
  });
});

describe("buscar a dónde ir", () => {
  it("primero por el nombre de la zona, sin tildes ni mayúsculas y con cualquier grafía", () => {
    expect(ids("Cusco")).toEqual([36, 4]); // y Machupicchu Pueblo, por su región
    expect(ids("machu picchu")).toEqual([4]);
    expect(ids("MACHUPICCHU")).toEqual([4]);
    expect(ids("trujillo")).toEqual([139]);
  });

  it("por un lugar de la zona, primero el más importante, y dice cuál", () => {
    const colca = buscarZonas(DESTINOS, "colca");
    expect(colca.map((e) => [e.zona.id, e.por, e.lugar])).toEqual([
      [71, "lugar", "Valle del Colca"],
      [147, "lugar", "Cañon del Colca"],
    ]);
    expect(buscarZonas(DESTINOS, "chan chan")[0]).toEqual({
      zona: zona(139),
      por: "lugar",
      lugar: "Complejo Arqueológico Chan Chan",
    });
    expect(buscarZonas(DESTINOS, "lima")[0]?.lugar).toBe("Centro Histórico de Lima");
  });

  it("desde el comienzo de una palabra: «ica» es Ica, no «Basílica»", () => {
    expect(buscarZonas(DESTINOS, "ica").map((e) => [e.zona.id, e.por])).toEqual([[27, "region"]]);
    expect(ids("silica")).toEqual([]);
  });

  it("con dos letras busca en los nombres y las regiones, no en los lugares", () => {
    expect(ids("cu")).toEqual([36, 4]);
    expect(ids("co")).toEqual([]);
  });

  it("sin nada escrito, o sin nada que coincida, no hay zonas", () => {
    expect(ids("")).toEqual([]);
    expect(ids("  ")).toEqual([]);
    expect(ids("wxyz")).toEqual([]);
  });

  it("sin nada escrito, propone las de algún imperdible de jerarquía 4, menos las de su ciudad", () => {
    const destacadas = (origen: string, cuantas?: number) =>
      zonasDestacadas(DESTINOS, origen, cuantas).map((e) => e.zona.id);
    expect(destacadas("lima")).toEqual([36, 139, 27, 4, 71]);
    expect(destacadas("cusco")).toEqual([31, 139, 27, 4, 71]);
    expect(destacadas("lima", 2)).toEqual([36, 139]);
  });

  it("debajo de su nombre dice por qué salió, o su lugar más importante", () => {
    const nota = (e: Partial<Encontrada> & { zona: Zona }) => notaDeZona({ por: null, lugar: null, ...e });
    expect(nota({ zona: zona(71), por: "lugar", lugar: "Valle del Colca" })).toBe("Por Valle del Colca");
    expect(nota({ zona: zona(36), por: "region" })).toBe("Cusco y Apurímac");
    expect(nota({ zona: zona(36), por: "nombre" })).toBe("Centro Histórico del Cusco");
    expect(nota({ zona: zona(147) })).toBe("Arequipa"); // sin imperdibles, su región
    expect(lugarPrincipal(zona(33))).toBe("Convento de Santa Rosa de Ocopa");
    expect(lugarPrincipal(zona(147))).toBeNull();
  });

  it("nombra la zona elegida si la lista llegó y la tiene", () => {
    expect(nombreDeZona(DESTINOS, 36)).toBe("Cuzco");
    expect(nombreDeZona(DESTINOS, 999)).toBeNull();
    expect(nombreDeZona(null, 36)).toBeNull();
    expect(nombreDeZona(undefined, 36)).toBeNull();
    expect(nombreDeZona(DESTINOS, null)).toBeNull();
  });
});

describe("con la lista publicada", () => {
  const lista = publicada as Destinos;
  const primeras = (texto: string, cuantas = 1) =>
    buscarZonas(lista, texto, cuantas).map((e) => [e.zona.nombre, e.lugar]);

  it("encuentra lo que más se busca", () => {
    expect(primeras("cusco", 3)).toEqual([
      ["Cuzco", null],
      ["Urubamba", null],
      ["Machupicchu Pueblo", null],
    ]);
    expect(primeras("machu picchu")).toEqual([["Machupicchu Pueblo", null]]);
    expect(primeras("colca")).toEqual([["Yanque", "Valle del Colca"]]);
    expect(primeras("mancora")).toEqual([["Máncora", null]]);
    expect(primeras("huaraz")).toEqual([["Huaraz", null]]);
    expect(primeras("titicaca")[0]?.[0]).toBe("Puno"); // por un lugar que lo escribe «Titikaka»
    expect(primeras("kuelap")).toEqual([["Chachapoyas", "Zona Arqueológica Monumental Kuélap"]]);
  });

  it("propone, sin nada escrito, ocho zonas de imperdibles, y desde Lima ninguna de Lima", () => {
    const desdeLima = zonasDestacadas(lista, "lima").map((e) => e.zona);
    expect(desdeLima).toHaveLength(8);
    expect(desdeLima.some((z) => z.misma_ciudad.includes("lima"))).toBe(false);
    expect(desdeLima[0]?.nombre).toBe("Cuzco");
  });
});
