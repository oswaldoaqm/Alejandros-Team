// Reproductor estilo Instagram Stories para el recorrido en video de DreemGO.
// Contiene los 8 momentos en una sola ventanita interactiva con auto-avance,
// barras de progreso segmentadas arriba, zonas táctiles (tocar izq/der),
// atajos de teclado (← / → / Espacio) y bandeja de historias destacadas abajo.

import { useCallback, useEffect, useRef, useState } from "react";
import { MarcaFlor } from "./Flor";
import { Icono, type NombreDeIcono } from "./Icono";

export interface PasoVideo {
  id: number;
  numero: string;
  titulo: string;
  etiqueta: string;
  inicio: number; // segundos
  fin: number; // segundos
  tiempoTexto: string;
  descripcion: string;
  icono: NombreDeIcono;
}

export const PASOS_VIDEO: readonly PasoVideo[] = [
  {
    id: 1,
    numero: "Paso 1",
    titulo: "El inicio",
    etiqueta: "Portada y bienvenida",
    inicio: 6,
    fin: 21,
    tiempoTexto: "0:06 - 0:21",
    descripcion:
      "Presentación de DreemGO y la propuesta de valor: tres viajes por el Perú día por día adaptados a lo que le pidas, con verificación en fuentes oficiales.",
    icono: "mochila",
  },
  {
    id: 2,
    numero: "Paso 2",
    titulo: "La consulta",
    etiqueta: "Formulario y filtros",
    inicio: 21,
    fin: 42,
    tiempoTexto: "0:21 - 0:42",
    descripcion:
      "Configuración de origen, mes, cantidad de días, intereses de viaje (gastronomía, naturaleza, historia), presupuesto máximo y límite de altura.",
    icono: "ajustes",
  },
  {
    id: 3,
    numero: "Paso 3",
    titulo: "Tres viajes para ti",
    etiqueta: "Ranking y selección",
    inicio: 43,
    fin: 52,
    tiempoTexto: "0:43 - 0:52",
    descripcion:
      "El algoritmo presenta las tres mejores zonas del país ordenadas por conveniencia, mostrando costo estimado por persona, tiempo de ida y estacionalidad del clima.",
    icono: "estrella",
  },
  {
    id: 4,
    numero: "Paso 4",
    titulo: "El viaje a Huaraz",
    etiqueta: "Itinerario y mapa",
    inicio: 53,
    fin: 80,
    tiempoTexto: "0:53 - 1:20",
    descripcion:
      "Detalle día por día en Huaraz: horarios precisos, paradas con jerarquías oficiales de MINCETUR, restaurantes cercanos en OpenStreetMap y mapa interactivo.",
    icono: "mapa",
  },
  {
    id: 5,
    numero: "Paso 5",
    titulo: "La misma consulta en febrero",
    etiqueta: "Clima y 10 años ERA5",
    inicio: 81,
    fin: 98,
    tiempoTexto: "1:21 - 1:38",
    descripcion:
      "Al consultar para febrero, el modelo analiza 10 años de precipitación histórica (Copernicus / Open-Meteo) y alerta sobre meses desaconsejados por temporada de lluvias.",
    icono: "lluvia",
  },
  {
    id: 6,
    numero: "Paso 6",
    titulo: "Machu Picchu en 2 días, en julio",
    etiqueta: "Destino fijo y vuelos",
    inicio: 99,
    fin: 130,
    tiempoTexto: "1:39 - 2:10",
    descripcion:
      "Búsqueda con destino fijo: evalúa la viabilidad de los días pedidos, conecta por avión para trayectos largos y arma el itinerario optimizado para la zona.",
    icono: "avion",
  },
  {
    id: 7,
    numero: "Paso 7",
    titulo: "El viaje se guarda",
    etiqueta: "Guardados y privacidad",
    inicio: 131,
    fin: 146,
    tiempoTexto: "2:11 - 2:26",
    descripcion:
      "Los viajes favoritos se guardan localmente en tu navegador sin requerir cuentas ni contraseñas. Toda la consulta viaja en el enlace para compartir fácilmente.",
    icono: "guardar",
  },
  {
    id: 8,
    numero: "Paso 8",
    titulo: "Un municipio publica un evento",
    etiqueta: "Eventos oficiales",
    inicio: 147,
    fin: 194,
    tiempoTexto: "2:27 - 3:14",
    descripcion:
      "Plataforma para que municipalidades y oficinas de turismo publiquen festividades y ferias oficiales, integrándolas al itinerario de quienes visiten la zona.",
    icono: "calendario",
  },
];

function reproducirSeguro(video: HTMLVideoElement, alIniciar: () => void, alFallar: () => void) {
  try {
    const promesa = video.play();
    if (promesa !== undefined && typeof promesa.then === "function") {
      promesa.then(alIniciar).catch(alFallar);
    } else {
      alIniciar();
    }
  } catch {
    alFallar();
  }
}

const PRIMER_PASO = PASOS_VIDEO[0] as PasoVideo;

export function VideoGuia() {
  const [indiceActivo, setIndiceActivo] = useState(0);
  const [estaReproduciendo, setEstaReproduciendo] = useState(false);
  const [progresoPaso, setProgresoPaso] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const pasoActual = PASOS_VIDEO[indiceActivo] ?? PRIMER_PASO;

  const irAlPaso = useCallback((nuevoIndice: number, autoReproducir = true) => {
    const i = Math.max(0, Math.min(PASOS_VIDEO.length - 1, nuevoIndice));
    setIndiceActivo(i);
    setProgresoPaso(0);
    const video = videoRef.current;
    if (video) {
      const pasoDestino = PASOS_VIDEO[i] ?? PRIMER_PASO;
      video.currentTime = pasoDestino.inicio;
      if (autoReproducir) {
        reproducirSeguro(
          video,
          () => setEstaReproduciendo(true),
          () => setEstaReproduciendo(false),
        );
      } else {
        video.pause();
        setEstaReproduciendo(false);
      }
    }
  }, []);

  const alActualizarTiempo = () => {
    const video = videoRef.current;
    if (!video) return;

    const tiempo = video.currentTime;

    // Si llegó al final del fragmento del paso actual:
    if (tiempo >= pasoActual.fin) {
      if (indiceActivo < PASOS_VIDEO.length - 1) {
        // Auto-avanzar a la siguiente historia (comportamiento clásico de Instagram Stories)
        irAlPaso(indiceActivo + 1, true);
      } else {
        // Al culminar la última historia (Paso 8), rebobinar al Paso 1 y pausar
        video.pause();
        video.currentTime = PRIMER_PASO.inicio;
        setEstaReproduciendo(false);
        setIndiceActivo(0);
        setProgresoPaso(0);
      }
      return;
    }

    // Calcular el porcentaje 0..100 de la barrita de la historia activa
    const duracion = pasoActual.fin - pasoActual.inicio;
    if (duracion > 0) {
      const pct = Math.min(100, Math.max(0, ((tiempo - pasoActual.inicio) / duracion) * 100));
      setProgresoPaso(pct);
    }
  };

  const alternarReproduccion = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused || !estaReproduciendo) {
      if (video.currentTime < pasoActual.inicio || video.currentTime >= pasoActual.fin) {
        video.currentTime = pasoActual.inicio;
      }
      reproducirSeguro(
        video,
        () => setEstaReproduciendo(true),
        () => setEstaReproduciendo(false),
      );
    } else {
      video.pause();
      setEstaReproduciendo(false);
    }
  }, [estaReproduciendo, pasoActual.inicio, pasoActual.fin]);

  // Tocar o hacer clic al lado izquierdo de la historia
  const alTocarIzquierda = useCallback(() => {
    const video = videoRef.current;
    // Si la historia actual ya lleva más de 2 segundos, se reinicia (igual que IG)
    if (video && video.currentTime - pasoActual.inicio > 2) {
      video.currentTime = pasoActual.inicio;
      setProgresoPaso(0);
    } else if (indiceActivo > 0) {
      irAlPaso(indiceActivo - 1, true);
    } else {
      if (video) video.currentTime = pasoActual.inicio;
      setProgresoPaso(0);
    }
  }, [indiceActivo, pasoActual.inicio, irAlPaso]);

  // Tocar o hacer clic al lado derecho de la historia
  const alTocarDerecha = useCallback(() => {
    if (indiceActivo < PASOS_VIDEO.length - 1) {
      irAlPaso(indiceActivo + 1, true);
    } else {
      irAlPaso(0, true);
    }
  }, [indiceActivo, irAlPaso]);

  // Control con teclas de flechas (← y →) y barra espaciadora
  useEffect(() => {
    const alPresionarTecla = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        alTocarDerecha();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        alTocarIzquierda();
      } else if (e.key === " " && (e.target as HTMLElement)?.tagName !== "BUTTON") {
        e.preventDefault();
        alternarReproduccion();
      }
    };
    window.addEventListener("keydown", alPresionarTecla);
    return () => window.removeEventListener("keydown", alPresionarTecla);
  }, [alTocarDerecha, alTocarIzquierda, alternarReproduccion]);

  // Al montar, inicializar el video en el segundo del primer fragmento para no mostrar la portada
  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = PRIMER_PASO.inicio;
    }
  }, []);

  return (
    <div className="stories-contenedor">
      {/* ── Historias destacadas (Highlights por encima de la ventanita) ──── */}
      <div className="stories-destacadas-bloque">
        <div className="stories-destacadas-encabezado">
          <span className="stories-destacadas-titulo">Historias destacadas</span>
          <span className="stories-destacadas-sub">Salta a cualquier momento del tutorial</span>
        </div>

        <div className="stories-destacadas" role="tablist" aria-label="Historias destacadas del tutorial">
          {PASOS_VIDEO.map((paso, idx) => {
            const esActivo = idx === indiceActivo;
            return (
              <button
                key={paso.id}
                type="button"
                role="tab"
                aria-selected={esActivo}
                className={`stories-destacada ${esActivo ? "stories-destacada--activo" : ""}`}
                onClick={() => irAlPaso(idx, true)}
                title={`Ver ${paso.numero}: ${paso.titulo}`}
                aria-label={`Ver ${paso.numero}: ${paso.titulo}`}
              >
                <div className="stories-destacada__aro">
                  <div className="stories-destacada__circulo">
                    <Icono nombre={paso.icono} tamano={22} />
                  </div>
                </div>
                <span className="stories-destacada__numero">{paso.numero}</span>
                <span className="stories-destacada__etiqueta">{paso.titulo}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Ventanita de Stories estilo macOS ──────────────────────────────── */}
      <div className="stories-ventana">
        {/* Barra superior de la ventanita */}
        <div className="stories-ventana__barra">
          <div className="stories-ventana__botones" aria-hidden="true">
            <span className="stories-ventana__boton stories-ventana__boton--rojo" />
            <span className="stories-ventana__boton stories-ventana__boton--amarillo" />
            <span className="stories-ventana__boton stories-ventana__boton--verde" />
          </div>
          <span className="stories-ventana__titulo-barra">
            DreemGO Stories · {pasoActual.numero}: {pasoActual.titulo}
          </span>
          <span className="stories-ventana__contador">
            {indiceActivo + 1} de {PASOS_VIDEO.length}
          </span>
        </div>

        {/* Visor de la Historia (Pantalla 16:10 con overlays) */}
        <div className="stories-visor">
          {/* El video único con cache local */}
          <video
            ref={videoRef}
            src="./tutorial.mp4#t=6"
            className="stories-visor__video"
            playsInline
            muted
            preload="metadata"
            onLoadedMetadata={() => {
              if (videoRef.current) {
                videoRef.current.currentTime = PASOS_VIDEO[indiceActivo]?.inicio ?? 6;
              }
            }}
            onTimeUpdate={alActualizarTiempo}
            onEnded={() => alTocarDerecha()}
          >
            <track kind="captions" srcLang="es" label="Español" />
            Tu navegador no soporta video HTML5.
          </video>

          {/* Capa superior: Barritas de progreso estilo Instagram Stories + Perfil */}
          <div className="stories-visor__arriba">
            {/* Las 8 barritas de progreso */}
            <div className="stories-barras" role="tablist" aria-label="Progreso de historias">
              {PASOS_VIDEO.map((paso, idx) => {
                let ancho = "0%";
                if (idx < indiceActivo) {
                  ancho = "100%";
                } else if (idx === indiceActivo) {
                  ancho = `${progresoPaso}%`;
                }

                return (
                  <button
                    key={paso.id}
                    type="button"
                    role="tab"
                    aria-selected={idx === indiceActivo}
                    className={`stories-barra ${idx === indiceActivo ? "stories-barra--activa" : ""}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      irAlPaso(idx, true);
                    }}
                    title={`Ir al ${paso.numero}: ${paso.titulo}`}
                    aria-label={`${paso.numero}: ${paso.titulo}`}
                  >
                    <div className="stories-barra__relleno" style={{ width: ancho }} />
                  </button>
                );
              })}
            </div>

            {/* Cabecera del Story (Avatar + Título + Controles) */}
            <div className="stories-perfil">
              <div className="stories-perfil__usuario">
                <div className="stories-perfil__avatar">
                  <div className="stories-perfil__icono">
                    <MarcaFlor className="stories-perfil__flor" />
                  </div>
                </div>
                <div className="stories-perfil__texto">
                  <div className="stories-perfil__nombre-fila">
                    <strong className="stories-perfil__nombre">DreemGO</strong>
                    <span className="stories-perfil__verificado" title="Cuenta verificada">
                      ✓
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Botones de navegación laterales flotantes */}
          <button
            type="button"
            className="stories-nav-btn stories-nav-btn--izq"
            onClick={(e) => {
              e.stopPropagation();
              alTocarIzquierda();
            }}
            aria-label="Historia anterior"
            title="Historia anterior (Flecha izquierda)"
          >
            <Icono nombre="atras" tamano={20} />
          </button>

          <button
            type="button"
            className="stories-nav-btn stories-nav-btn--der"
            onClick={(e) => {
              e.stopPropagation();
              alTocarDerecha();
            }}
            aria-label="Siguiente historia"
            title="Siguiente historia (Flecha derecha)"
          >
            <Icono nombre="flecha" tamano={20} />
          </button>

          {/* Zonas táctiles invisibles (Tap Left, Tap Center, Tap Right como en IG) */}
          <div className="stories-tap-zonas">
            <button
              type="button"
              className="stories-tap-zona stories-tap-zona--izq"
              onClick={alTocarIzquierda}
              aria-label="Retroceder historia"
              tabIndex={-1}
            />
            <button
              type="button"
              className="stories-tap-zona stories-tap-zona--centro"
              onClick={alternarReproduccion}
              aria-label={estaReproduciendo ? "Pausar historia" : "Reproducir historia"}
              tabIndex={-1}
            />
            <button
              type="button"
              className="stories-tap-zona stories-tap-zona--der"
              onClick={alTocarDerecha}
              aria-label="Avanzar historia"
              tabIndex={-1}
            />
          </div>

          {/* Ícono gigante de Play cuando el video está pausado */}
          {!estaReproduciendo && (
            <button
              type="button"
              className="stories-play-overlay"
              onClick={alternarReproduccion}
              aria-label="Reproducir historia"
            >
              <div className="stories-play-circle">
                <Icono nombre="reproducir" tamano={28} />
              </div>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
