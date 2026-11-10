import { describe, expect, it } from "vitest";
import type { Polo, Recurso, Ruta } from "./api/tipos";
import {
  creditoDeFoto,
  type Foto,
  type Fotos,
  fotoDeLaZona,
  fotoDelViaje,
  licenciaDeFoto,
  paginaDeFoto,
  srcsetDeFoto,
  urlDeFoto,
} from "./fotos";

const COMMONS = "https://upload.wikimedia.org/wikipedia/commons";

function foto(archivo: string, ancho = 4000, alto = 3000, extra: Partial<Foto> = {}): Foto {
  return {
    archivo,
    ruta: "a/ab",
    ancho,
    alto,
    autor: "Ana Quispe",
    licencia: "CC BY-SA 4.0",
    url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
    wikidata: "Q1",
    ...extra,
  };
}

describe("las direcciones de una foto", () => {
  it("pide la miniatura del ancho justo, con el nombre como lo escribe Commons", () => {
    const f = foto("Plaza de Armas (Ayacucho).jpg");
    expect(urlDeFoto(f, 500)).toBe(
      `${COMMONS}/thumb/a/ab/Plaza_de_Armas_(Ayacucho).jpg/500px-Plaza_de_Armas_(Ayacucho).jpg`,
    );
    expect(paginaDeFoto(f)).toBe("https://commons.wikimedia.org/wiki/File:Plaza_de_Armas_(Ayacucho).jpg");
  });

  it("escapa lo que no puede ir en una dirección", () => {
    expect(urlDeFoto(foto("Iglesia de Ñaña #2.jpg"), 330)).toBe(
      `${COMMONS}/thumb/a/ab/Iglesia_de_%C3%91a%C3%B1a_%232.jpg/330px-Iglesia_de_%C3%91a%C3%B1a_%232.jpg`,
    );
  });

  it("si la original es más chica que lo pedido, va la original", () => {
    expect(urlDeFoto(foto("Chica.jpg", 800, 600), 960)).toBe(`${COMMONS}/a/ab/Chica.jpg`);
  });

  it("ofrece al navegador solo los anchos que Wikimedia sirve, hasta el tope", () => {
    const anchos = (srcset: string) => srcset.split(", ").map((s) => s.split(" ")[1]);
    expect(anchos(srcsetDeFoto(foto("Grande.jpg")))).toEqual(["330w", "500w", "960w", "1280w"]);
    expect(anchos(srcsetDeFoto(foto("Grande.jpg"), 500))).toEqual(["330w", "500w"]);
    // Una de 800 px: las miniaturas que caben y, en lugar de las más grandes, la original.
    expect(anchos(srcsetDeFoto(foto("Media.jpg", 800, 600)))).toEqual(["330w", "500w", "800w"]);
  });
});

describe("el crédito de una foto", () => {
  it("lleva su autor y su licencia", () => {
    expect(creditoDeFoto(foto("A.jpg"))).toBe("Foto: Ana Quispe, CC BY-SA 4.0");
  });

  it("una de dominio público lo dice en castellano, y sin autor no inventa uno", () => {
    const libre = foto("B.jpg", 4000, 3000, { autor: "", licencia: "Public domain" });
    expect(licenciaDeFoto(libre)).toBe("dominio público");
    expect(creditoDeFoto(libre)).toBe("Foto de dominio público");
  });

  it("la licencia que solo pide nombrar al autor también va en castellano", () => {
    const conAtribucion = { ...foto("A.jpg"), licencia: "Attribution", url_licencia: "" };
    expect(licenciaDeFoto(conAtribucion)).toBe("con atribución");
    expect(creditoDeFoto(conAtribucion)).toBe("Foto: Ana Quispe, con atribución");
  });
});

// ── Qué foto representa a un viaje y a una zona ─────────────────────────────────────

function lugar(codigo: string, jerarquia: number | null): Recurso {
  return { codigo, nombre: `Lugar ${codigo}`, jerarquia } as Recurso;
}

const POLO = { id: 7, base: { nombre: "Huancayo" } } as Polo;

function viaje(...dias: Recurso[][]): Ruta {
  return {
    polo: POLO,
    dias: dias.map((recursos) => ({ paradas: recursos.map((recurso) => ({ recurso })) })),
  } as Ruta;
}

function fotos(lugares: Record<string, Foto>, bases: Record<string, Foto> = {}): Fotos {
  return { version_datos: "2026.10.2", lugares, bases };
}

describe("la foto de un viaje", () => {
  it("es la de su imperdible más importante, aunque no sea el primero del viaje", () => {
    const ruta = viaje([lugar("1", 2), lugar("2", 3)], [lugar("3", 4)]);
    const elegida = fotoDelViaje(ruta, fotos({ "1": foto("1.jpg"), "2": foto("2.jpg"), "3": foto("3.jpg") }));
    expect(elegida).toEqual({ foto: foto("3.jpg"), de: "Lugar 3" });
  });

  it("entre los imperdibles prefiere una apaisada: en la tarjeta, una vertical se recorta demasiado", () => {
    const ruta = viaje([lugar("1", 4), lugar("2", 3)]);
    const elegida = fotoDelViaje(ruta, fotos({ "1": foto("1.jpg", 2000, 3000), "2": foto("2.jpg") }));
    expect(elegida?.de).toBe("Lugar 2");
  });

  it("si ningún imperdible tiene foto, va la del pueblo donde se duerme; después, la de cualquier lugar", () => {
    const ruta = viaje([lugar("1", 3), lugar("2", 2)]);
    const conBase = fotos({ "2": foto("2.jpg") }, { "7": foto("base.jpg") });
    expect(fotoDelViaje(ruta, conBase)).toEqual({ foto: foto("base.jpg"), de: "Huancayo" });
    expect(fotoDelViaje(ruta, fotos({ "2": foto("2.jpg") }))?.de).toBe("Lugar 2");
    expect(fotoDelViaje(ruta, fotos({}))).toBeNull();
  });

  it("la de una zona sigue el mismo orden", () => {
    const recursos = [lugar("1", 2), lugar("2", 3)];
    expect(fotoDeLaZona(POLO, recursos, fotos({ "1": foto("1.jpg"), "2": foto("2.jpg") }))?.de).toBe(
      "Lugar 2",
    );
    expect(fotoDeLaZona(POLO, recursos, fotos({ "1": foto("1.jpg") }, { "7": foto("base.jpg") }))?.de).toBe(
      "Huancayo",
    );
  });
});
