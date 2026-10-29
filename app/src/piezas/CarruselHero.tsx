// Carrusel de la portada: cinco destinos del Perú con su foto, su lema, una caligrafía decorativa
// y un botón que abre el viaje a esa zona. La forma (foto a todo el ancho, lema y botón) sigue a
// las páginas de turismo del Perú, como ytuqueplanes.com; los textos son propios. Las fotos son de
// Wikimedia Commons y cada una lleva su autor y su licencia, como en el resto de la app.

import { useCallback, useEffect, useRef, useState } from "react";
import { type Foto, urlDeFoto } from "../fotos";
import { CreditoDeFoto } from "./Foto";
import { Icono } from "./Icono";

export type IconoCaligrafiaTipo = "corazon" | "montana" | "volcan" | "ciudadela" | "balsa";

export interface DestinoCarrusel {
  id: string;
  destinoId: number;
  titulo: string;
  subtitulo: string;
  caligrafia: string;
  icono: IconoCaligrafiaTipo;
  botonTexto: string;
  foto: Foto;
  alt: string;
  lugar: string;
}

export const DESTINOS_HERO: DestinoCarrusel[] = [
  {
    id: "cusco",
    destinoId: 36,
    titulo: "Camina el Cusco a tu ritmo",
    subtitulo: "Saqsaywamán, el barrio de San Blas y la ciudad inca, en un plan armado día por día.",
    caligrafia: "Cusquito me encanta",
    icono: "corazon",
    botonTexto: "Explorar Cusco",
    foto: {
      archivo: "Cusco, Sacsayhuamán - panoramio.jpg",
      ruta: "5/53",
      ancho: 4912,
      alto: 1920,
      autor: "gertrudis2010",
      licencia: "CC BY-SA 3.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/3.0",
      wikidata: "",
    },
    alt: "Fortaleza ceremonial de Saqsaywamán en Cusco",
    lugar: "Cusco",
  },
  {
    id: "huaraz",
    destinoId: 14,
    titulo: "Conquista las lagunas turquesas y nevados de Huaraz",
    subtitulo: "Caminatas de alta montaña bajo el Huascarán, glaciares y el Callejón de Huaylas.",
    caligrafia: "Áncash te abraza",
    icono: "montana",
    botonTexto: "Explorar Huaraz",
    foto: {
      archivo: "Huascaran Huandoy Chopicalqui seen from Huaraz.JPG",
      ruta: "2/2f",
      ancho: 3648,
      alto: 2736,
      autor: "Uwebart",
      licencia: "CC BY-SA 3.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/3.0",
      wikidata: "",
    },
    alt: "Nevados Huascarán y Chopicalqui desde Huaraz",
    lugar: "Áncash",
  },
  {
    id: "arequipa",
    destinoId: 40,
    titulo: "Siente la magia blanca y volcanes de Arequipa",
    subtitulo: "Arquitectura de sillar, el majestuoso Cañón del Colca y su tradición culinaria.",
    caligrafia: "Arequipa bonita",
    icono: "volcan",
    botonTexto: "Visitar Arequipa",
    foto: {
      archivo: "Arequipa, Plaza de Armas, 2023 (10).jpg",
      ruta: "2/22",
      ancho: 6960,
      alto: 4640,
      autor: "Draceane",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "",
    },
    alt: "Plaza de Armas y volcán Misti en Arequipa",
    lugar: "Arequipa",
  },
  {
    id: "machupicchu",
    destinoId: 4,
    titulo: "Explora la energía milenaria de Machupicchu",
    subtitulo: "La maravilla del mundo entre orquídeas, montañas sagradas y caminos incas.",
    caligrafia: "Mágica ciudadela",
    icono: "ciudadela",
    botonTexto: "Ir a Machupicchu",
    foto: {
      archivo: "Machu Picchu, Peru - Laslovarga (262).jpg",
      ruta: "2/24",
      ancho: 5184,
      alto: 3456,
      autor: "Laslovarga",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "",
    },
    alt: "Santuario Histórico de Machupicchu",
    lugar: "Cusco",
  },
  {
    id: "puno",
    destinoId: 11,
    titulo: "Navega sobre el lago sagrado y las islas de Puno",
    subtitulo: "Cultura viva en las islas de los Uros y Taquile, en las aguas más altas del mundo.",
    caligrafia: "Titicaca legendario",
    icono: "balsa",
    botonTexto: "Descubrir Puno",
    foto: {
      archivo: "Vista de Puno y el Titicaca, Perú, 2015-08-01, DD 53-54 PAN.JPG",
      ruta: "4/42",
      ancho: 10214,
      alto: 4096,
      autor: "Diego Delso",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "",
    },
    alt: "Vista panorámica de Puno y el Lago Titicaca",
    lugar: "Puno",
  },
];

function IconoCaligrafia({ tipo }: { tipo: IconoCaligrafiaTipo }) {
  switch (tipo) {
    case "corazon":
      return (
        <svg
          viewBox="0 0 64 64"
          width="76"
          height="76"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="carrusel-hero__caligrafia-svg"
          aria-hidden="true"
        >
          {/* Silueta del corazón con relleno suave */}
          <path
            d="M32 56 C14 43 6 31 6 20 C6 12 12 6 21 6 C26 6 29.5 9 32 13 C34.5 9 38 6 43 6 C52 6 58 12 58 20 C58 31 50 43 32 56 Z"
            fill="currentColor"
            fillOpacity="0.22"
          />
          {/* Chacana andina (cruz escalonada inca) en el corazón */}
          <path
            d="M28 20 H36 V24 H40 V28 H44 V36 H40 V40 H36 V44 H28 V40 H24 V36 H20 V28 H24 V24 H28 Z"
            fill="currentColor"
            fillOpacity="0.35"
            strokeWidth="1.8"
          />
          {/* Núcleo sagrado de la Chacana */}
          <circle cx="32" cy="32" r="2.5" fill="currentColor" stroke="none" />
          {/* Destellos de luz y calidez cusqueña */}
          <path d="M52 10 L54 6 M58 14 L62 13 M6 14 L2 13 M12 10 L10 6" strokeWidth="1.8" />
        </svg>
      );
    case "montana":
      return (
        <svg
          viewBox="0 0 64 64"
          width="76"
          height="76"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="carrusel-hero__caligrafia-svg"
          aria-hidden="true"
        >
          {/* Picos nevados del Huascarán (Norte y Sur) */}
          <path d="M4 50 L24 10 L38 28 L48 18 L60 50 Z" fill="currentColor" fillOpacity="0.22" />
          {/* Casquetes glaciares con líneas de nieve facetadas */}
          <path d="M19 20 L24 10 L29 20 L25 24 L20 22 Z" fill="currentColor" fillOpacity="0.4" />
          <path d="M43 23 L48 18 L53 25 L49 27 L45 25 Z" fill="currentColor" fillOpacity="0.4" />
          {/* Aristas y grietas del glaciar */}
          <path d="M24 24 V38 M48 27 V42" strokeWidth="1.8" />
          <path d="M15 35 L24 38 L32 33" strokeWidth="1.8" />
          <path d="M38 28 L48 42 L55 38" strokeWidth="1.8" />
          {/* Laguna turquesa glaciar en la base con ondas */}
          <path d="M8 50 C16 48 24 52 32 50 C40 48 48 52 56 50" strokeWidth="2.2" />
          <path d="M14 56 C20 54 26 57 32 55 C38 53 44 57 50 55" strokeWidth="1.8" strokeOpacity="0.75" />
        </svg>
      );
    case "volcan":
      return (
        <svg
          viewBox="0 0 64 64"
          width="76"
          height="76"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="carrusel-hero__caligrafia-svg"
          aria-hidden="true"
        >
          {/* Cono volcánico del Misti */}
          <path d="M8 52 L26 16 H38 L56 52 Z" fill="currentColor" fillOpacity="0.22" />
          {/* Cráter y nieve cumbrera */}
          <path d="M26 16 H38" strokeWidth="2.5" />
          <path
            d="M22 24 L26 16 L31 22 L34 16 L38 16 L42 24 L36 26 L30 24 Z"
            fill="currentColor"
            fillOpacity="0.4"
          />
          {/* Fumarola y penacho de vapor volcánico */}
          <path d="M29 11 C28 7 30 4 33 4 C36 4 35 1 37 1" strokeWidth="1.8" />
          <path d="M34 12 C35 9 37 7 40 7" strokeWidth="1.8" strokeDasharray="2 3" />
          {/* Arquería colonial de sillar de Yanahuara en la base */}
          <path d="M12 52 V44 C12 40 18 40 18 44 V52" fill="currentColor" fillOpacity="0.3" />
          <path d="M22 52 V42 C22 37 32 37 32 42 V52" fill="currentColor" fillOpacity="0.3" />
          <path d="M32 52 V42 C32 37 42 37 42 42 V52" fill="currentColor" fillOpacity="0.3" />
          <path d="M46 52 V44 C46 40 52 40 52 44 V52" fill="currentColor" fillOpacity="0.3" />
          <path d="M8 52 H56" strokeWidth="2.5" />
        </svg>
      );
    case "ciudadela":
      return (
        <svg
          viewBox="0 0 64 64"
          width="76"
          height="76"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="carrusel-hero__caligrafia-svg"
          aria-hidden="true"
        >
          {/* Silueta de Huayna Picchu y pico secundario */}
          <path d="M6 52 L22 14 L33 28 L42 21 L58 52 Z" fill="currentColor" fillOpacity="0.22" />
          <path d="M22 14 L27 24 L33 28" />
          <path d="M42 21 L47 31" />
          {/* Terrazas y andenes incas escalonados */}
          <path d="M12 52 H54" strokeWidth="2.5" />
          <path d="M15 46 H50" />
          <path d="M19 40 H45" />
          <path d="M24 34 H39" />
          {/* Muros verticales de contención de los andenes */}
          <path d="M26 46 V52 M38 46 V52 M46 46 V52" strokeWidth="1.5" />
          <path d="M22 40 V46 M34 40 V46 M42 40 V46" strokeWidth="1.5" />
          <path d="M28 34 V40 M36 34 V40" strokeWidth="1.5" />
          {/* Sol sagrado Inti sobre la ciudadela */}
          <circle cx="49" cy="13" r="4.5" fill="currentColor" fillOpacity="0.3" />
          <path
            d="M49 5 V8 M49 18 V21 M41 13 H44 M54 13 H57 M43.5 7.5 L45.8 9.8 M52.2 16.2 L54.5 18.5 M43.5 18.5 L45.8 16.2 M52.2 9.8 L54.5 7.5"
            strokeWidth="1.8"
          />
        </svg>
      );
    case "balsa":
      return (
        <svg
          viewBox="0 0 64 64"
          width="76"
          height="76"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="carrusel-hero__caligrafia-svg"
          aria-hidden="true"
        >
          {/* Casco tradicional de totora curvada con proa zoomorfa alzada */}
          <path
            d="M6 38 C12 43 28 47 48 46 C56 46 60 41 60 36 C54 38 42 40 28 40 C16 40 8 38 6 38 Z"
            fill="currentColor"
            fillOpacity="0.3"
          />
          <path d="M6 38 C12 43 28 47 48 46 C56 46 60 41 60 36" strokeWidth="2.5" />
          {/* Proa de totora estilizada (cabeza tradicional de puma) */}
          <path
            d="M56 38 C58 35 60 28 58 22 C55 23 53 26 54 30"
            strokeWidth="2"
            fill="currentColor"
            fillOpacity="0.3"
          />
          {/* Mástil y vela de totora tejida */}
          <path d="M22 14 L28 38 M34 14 L28 38" strokeWidth="2" />
          <path d="M28 15 L44 26 H28 Z" fill="currentColor" fillOpacity="0.35" strokeWidth="2" />
          <path d="M28 19 L38 26 M28 23 L33 26" strokeWidth="1.4" />
          {/* Remos tradicionales */}
          <path d="M18 36 L10 46" strokeWidth="2" />
          <ellipse cx="9" cy="47" rx="3" ry="1.5" transform="rotate(-40 9 47)" fill="currentColor" />
          {/* Olas del lago Titicaca */}
          <path d="M4 52 C12 50 18 54 26 52 C34 50 40 54 48 52 C54 50 58 52 62 51" strokeWidth="2.2" />
          <path
            d="M10 57 C16 55 22 58 28 56 C34 54 40 58 46 56 C52 54 56 56 60 55"
            strokeWidth="1.6"
            strokeOpacity="0.7"
          />
        </svg>
      );
  }
}

interface Props {
  onElegirDestino?: (destinoId: number) => void;
}

/** Si la persona pidió menos movimiento: entonces el carrusel arranca detenido. */
function pideMenosMovimiento(): boolean {
  return (
    typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true
  );
}

export function CarruselHero({ onElegirDestino }: Props) {
  const [activo, ponerActivo] = useState(0);
  // `pausado`: mientras el puntero o el foco están encima. `detenido`: si el usuario pidió menos movimiento en su sistema.
  const [pausado, ponerPausado] = useState(false);
  const [detenido] = useState(pideMenosMovimiento);
  // Las fotos que ya se pidieron: la que se ve y, si pasa solo, la que sigue. No las cinco de golpe.
  const [pedidas, ponerPedidas] = useState<ReadonlySet<number>>(() => new Set([0]));
  const inicioToque = useRef<number | null>(null);
  const proxima = (activo + 1) % DESTINOS_HERO.length;
  const pedir = (i: number) => i === activo || (i === proxima && !detenido) || pedidas.has(i);

  const siguiente = useCallback(() => {
    ponerActivo((actual) => (actual + 1) % DESTINOS_HERO.length);
  }, []);

  const anterior = useCallback(() => {
    ponerActivo((actual) => (actual - 1 + DESTINOS_HERO.length) % DESTINOS_HERO.length);
  }, []);

  const irA = (indice: number) => {
    ponerActivo(indice);
  };

  // Pasa solo cada 6,5 segundos, salvo que esté en pausa o detenido.
  useEffect(() => {
    if (pausado || detenido) return;
    const temporizador = window.setInterval(siguiente, 6500);
    return () => window.clearInterval(temporizador);
  }, [pausado, detenido, siguiente]);

  useEffect(() => {
    const nuevas = detenido ? [activo] : [activo, proxima];
    ponerPedidas((antes) => (nuevas.every((i) => antes.has(i)) ? antes : new Set([...antes, ...nuevas])));
  }, [activo, proxima, detenido]);

  const alTocarInicio = (e: React.TouchEvent) => {
    inicioToque.current = e.touches[0]?.clientX ?? null;
  };

  const alTocarFin = (e: React.TouchEvent) => {
    if (inicioToque.current === null) return;
    const fin = e.changedTouches[0]?.clientX ?? 0;
    const diff = inicioToque.current - fin;
    if (Math.abs(diff) > 40) {
      if (diff > 0) siguiente();
      else anterior();
    }
    inicioToque.current = null;
  };

  const actual = DESTINOS_HERO[activo] ?? DESTINOS_HERO[0];
  if (!actual) return null;

  return (
    <section
      className="carrusel-hero"
      aria-roledescription="carrusel"
      aria-label="Destinos destacados del Perú"
      onMouseEnter={() => ponerPausado(true)}
      onMouseLeave={() => ponerPausado(false)}
      onFocus={() => ponerPausado(true)}
      onBlur={() => ponerPausado(false)}
      onTouchStart={alTocarInicio}
      onTouchEnd={alTocarFin}
    >
      <div className="carrusel-hero__contenedor">
        {DESTINOS_HERO.map((dest, i) => {
          const visible = i === activo;
          return (
            <div
              key={dest.id}
              className={`carrusel-hero__diapositiva${visible ? " carrusel-hero__diapositiva--activa" : ""}`}
              aria-hidden={!visible}
            >
              {pedir(i) ? (
                <img
                  src={urlDeFoto(dest.foto, 1280)}
                  alt={dest.alt}
                  className="carrusel-hero__fondo"
                  fetchPriority={i === 0 ? "high" : "low"}
                  decoding="async"
                />
              ) : null}
              <div className="carrusel-hero__degradado" aria-hidden="true" />
            </div>
          );
        })}

        <div className="carrusel-hero__contenido">
          {/* Mientras pasa solo no se anuncia cada cambio; detenido o en pausa, sí. */}
          <div className="carrusel-hero__texto" aria-live={pausado || detenido ? "polite" : "off"}>
            <span className="carrusel-hero__etiqueta">
              <Icono nombre="pin" tamano={14} />
              {actual.lugar} · Perú
            </span>
            <h2 className="carrusel-hero__titulo">{actual.titulo}</h2>
            <p className="carrusel-hero__subtitulo">{actual.subtitulo}</p>
            {onElegirDestino ? (
              <button
                type="button"
                className="carrusel-hero__boton"
                onClick={() => onElegirDestino(actual.destinoId)}
              >
                {actual.botonTexto}
                <Icono nombre="flecha" tamano={18} />
              </button>
            ) : null}
          </div>

          <aside className="carrusel-hero__caligrafia" aria-hidden="true">
            <span className="carrusel-hero__caligrafia-texto">{actual.caligrafia}</span>
            <span className="carrusel-hero__caligrafia-icono-caja">
              <IconoCaligrafia tipo={actual.icono} />
            </span>
          </aside>
        </div>

        {/* Flechas de navegación */}
        <button
          type="button"
          className="carrusel-hero__flecha carrusel-hero__flecha--anterior"
          onClick={anterior}
          aria-label="Destino anterior"
        >
          <Icono nombre="atras" tamano={24} />
        </button>
        <button
          type="button"
          className="carrusel-hero__flecha carrusel-hero__flecha--siguiente"
          onClick={siguiente}
          aria-label="Siguiente destino"
        >
          <Icono nombre="flecha" tamano={24} />
        </button>

        <p className="carrusel-hero__credito">
          <CreditoDeFoto foto={actual.foto} />
        </p>

        <div className="carrusel-hero__mandos">
          {/* Indicadores de diapositiva (pills) */}
          <div className="carrusel-hero__indicadores" role="tablist" aria-label="Destinos del carrusel">
            {DESTINOS_HERO.map((dest, i) => (
              <button
                key={dest.id}
                type="button"
                role="tab"
                aria-selected={i === activo}
                aria-label={`Ver diapositiva ${i + 1}: ${dest.lugar}`}
                className={`carrusel-hero__indicador${i === activo ? " carrusel-hero__indicador--activo" : ""}`}
                onClick={() => irA(i)}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
