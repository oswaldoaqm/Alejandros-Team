import { useEffect, useRef, useState } from "react";
import { Icono } from "./Icono";

export interface InsigniaJerarquiaProps {
  /** Nivel de jerarquía según MINCETUR (1 a 4). DreemGO destaca 3 y 4. */
  jerarquia: number;
  /** Variante visual: "insignia" (para la ficha de lugar) o "sello" (para la tarjeta de ruta). */
  variante?: "insignia" | "sello";
  /** Contexto donde se muestra, para adaptar el texto del pie. */
  contexto?: "lugar" | "ruta";
}

interface NivelInfo {
  nivel: number;
  alcance: string;
  resumen: string;
  descripcion: string;
  ejemplos?: string;
}

const NIVELES: Record<number, NivelInfo> = {
  4: {
    nivel: 4,
    alcance: "Internacional",
    resumen: "Atractivo de clase mundial",
    descripcion:
      "Recurso excepcional de valor universal. Capaz de motivar por sí solo importantes corrientes de turismo internacional hacia el Perú.",
    ejemplos: "Machupicchu, Líneas de Nasca, Lago Titicaca, Cañón del Colca",
  },
  3: {
    nivel: 3,
    alcance: "Nacional",
    resumen: "Gran significación nacional",
    descripcion:
      "Recurso con rasgos únicos de gran valor en el país. Motiva turismo interno y receptivo, por sí mismo o en conjunto con la región.",
    ejemplos: "Kuélap, Cordillera Blanca, Reserva Nal. de Paracas",
  },
  2: {
    nivel: 2,
    alcance: "Regional",
    resumen: "Interés regional o de circuito",
    descripcion:
      "Recurso atractivo para visitantes de la propia región o zonas limítrofes, complementando circuitos de viaje.",
  },
  1: {
    nivel: 1,
    alcance: "Local",
    resumen: "Interés local o comunal",
    descripcion: "Recurso de interés para la población local o cercana, con valor recreativo o formativo.",
  },
};

export function InsigniaJerarquia({
  jerarquia,
  variante = "insignia",
  contexto = "lugar",
}: InsigniaJerarquiaProps) {
  const [abierto, setAbierto] = useState(false);
  const contenedorRef = useRef<HTMLSpanElement>(null);
  const temporizadorRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const alEntrar = () => {
    if (temporizadorRef.current) {
      clearTimeout(temporizadorRef.current);
      temporizadorRef.current = null;
    }
    setAbierto(true);
  };

  const alSalir = () => {
    temporizadorRef.current = setTimeout(() => {
      setAbierto(false);
    }, 180);
  };

  const alternar = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (temporizadorRef.current) {
      clearTimeout(temporizadorRef.current);
      temporizadorRef.current = null;
    }
    setAbierto((prev) => !prev);
  };

  useEffect(() => {
    if (!abierto) return;

    const alPulsarFuera = (e: MouseEvent | TouchEvent) => {
      if (contenedorRef.current && !contenedorRef.current.contains(e.target as Node)) {
        setAbierto(false);
      }
    };

    const alPulsarTecla = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setAbierto(false);
      }
    };

    document.addEventListener("pointerdown", alPulsarFuera);
    document.addEventListener("keydown", alPulsarTecla);
    return () => {
      document.removeEventListener("pointerdown", alPulsarFuera);
      document.removeEventListener("keydown", alPulsarTecla);
    };
  }, [abierto]);

  const claseInsignia =
    variante === "sello"
      ? `viaje-tarjeta__sello viaje-tarjeta__sello--j${jerarquia}`
      : `insignia-jerarquia insignia-jerarquia--${jerarquia}`;

  const info = NIVELES[jerarquia] ?? {
    nivel: jerarquia,
    alcance: "Turístico",
    resumen: `Jerarquía ${jerarquia}`,
    descripcion: `Recurso clasificado con jerarquía ${jerarquia} en el inventario oficial del MINCETUR.`,
  };

  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: contenedor con eventos de cursor para sostener el globo visible
    <span
      ref={contenedorRef}
      className={`insignia-jerarquia-wrap ${abierto ? "insignia-jerarquia-wrap--abierto" : ""}`}
      onMouseEnter={alEntrar}
      onMouseLeave={alSalir}
    >
      {/* biome-ignore lint/a11y/useSemanticElements: dentro de un enlace <a> no es válido anidar un <button> */}
      <span
        role="button"
        tabIndex={0}
        className={claseInsignia}
        aria-expanded={abierto}
        aria-haspopup="dialog"
        aria-label={`Jerarquía ${jerarquia} · MINCETUR. Presiona o pasa el cursor para conocer qué significa esta jerarquía.`}
        onClick={alternar}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            alternar(e);
          }
        }}
      >
        <Icono nombre="escudo" tamano={12} />
        <span>Jerarquía {jerarquia} · MINCETUR</span>
      </span>

      {abierto ? (
        // biome-ignore lint/a11y/useKeyWithClickEvents: solo previene que el clic dentro del diálogo navegue el enlace padre
        <div
          className={`globo-jerarquia globo-jerarquia--j${jerarquia}`}
          role="dialog"
          aria-label={`Definición de Jerarquía ${jerarquia} del MINCETUR`}
          onClick={(e) => {
            // Evitar que un click dentro del globo navegue un enlace padre
            e.preventDefault();
            e.stopPropagation();
          }}
          onMouseEnter={alEntrar}
          onMouseLeave={alSalir}
        >
          <div className="globo-jerarquia__cabecera">
            <div className="globo-jerarquia__titulo-wrap">
              <Icono nombre="escudo" tamano={14} />
              <strong className="globo-jerarquia__titulo">Jerarquía {info.nivel} · MINCETUR</strong>
            </div>
            <button
              type="button"
              className="globo-jerarquia__boton-cerrar"
              aria-label="Cerrar explicación de jerarquía"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setAbierto(false);
              }}
            >
              <Icono nombre="cerrar" tamano={13} />
            </button>
          </div>

          <div className="globo-jerarquia__etiqueta-fila">
            <span className={`globo-jerarquia__pill globo-jerarquia__pill--j${info.nivel}`}>
              {info.alcance}
            </span>
            <span className="globo-jerarquia__resumen">{info.resumen}</span>
          </div>

          <p className="globo-jerarquia__descripcion">{info.descripcion}</p>

          {info.ejemplos ? (
            <p className="globo-jerarquia__ejemplos">
              <strong>Ejemplos:</strong> {info.ejemplos}.
            </p>
          ) : null}

          <div className="globo-jerarquia__pie">
            <p>
              {contexto === "ruta"
                ? "Esta ruta incluye al menos un atractivo con esta máxima distinción."
                : "Calificación oficial según el inventario turístico del MINCETUR."}
            </p>
          </div>
        </div>
      ) : null}
    </span>
  );
}
