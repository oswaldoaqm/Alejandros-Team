// Cómo funciona DreemGO, de dónde salen sus datos y qué no hace.
// Tour guiado en video por pasos dentro de su propia ventana interactiva, más documentación técnica.

import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { Enlace, EnlaceExterno } from "../piezas/Enlace";
import { Icono } from "../piezas/Icono";
import { VideoGuia } from "../piezas/VideoGuia";
import { enlaces } from "../ruta";

const REPOSITORIO = "https://github.com/oswaldoaqm/Alejandros-Team";
const CDC_ALTURA =
  "https://www.cdc.gov/yellow-book/hcp/environmental-hazards-risks/high-altitude-travel-and-altitude-illness.html";

export function Acerca() {
  const { opciones } = useApp();
  useTitulo("Cómo funciona");

  /** Acordeón exclusivo: al abrir una sección se cierran automáticamente las demás */
  const alCambiarAcordeon = (e: React.SyntheticEvent<HTMLDetailsElement>) => {
    const actual = e.currentTarget;
    if (!actual.open) return;
    const contenedor = actual.closest(".acerca-acordeones");
    if (!contenedor) return;
    const todos = contenedor.querySelectorAll<HTMLDetailsElement>("details.acerca-acordeon");
    for (const d of todos) {
      if (d !== actual && d.open) {
        d.open = false;
      }
    }
  };

  return (
    <>
      <header className="pagina-hero">
        <span className="pagina-hero__icono">
          <Icono nombre="info" tamano={36} />
        </span>
        <h1 tabIndex={-1} className="pagina-hero__titulo">
          Cómo funciona
        </h1>
        <p className="pagina-hero__bajada">
          DreemGO propone hasta tres viajes dentro del Perú para lo que le pidas, día por día. No vende ni
          reserva: estima con datos abiertos y te deja verificar cada lugar en su fuente oficial.
        </p>
      </header>

      <div className="acerca-contenedor">
        {/* ── Tour Guiado en Video por Pasos (Ventanita interactiva) ─────── */}
        <section className="acerca-seccion" aria-labelledby="titulo-tour-video">
          <div className="acerca-seccion__cabeza">
            <h2 id="titulo-tour-video" className="acerca-seccion__titulo">
              Recorrido de la app paso a paso
            </h2>
            <p className="acerca-seccion__bajada">
              Explora en la ventana interactiva los 8 momentos clave de DreemGO al estilo historias. Toca los
              laterales o usa las flechas del teclado para navegar entre pasos, o selecciona cualquier
              historia destacada para saltar directamente a ese fragmento en video.
            </p>
          </div>

          <VideoGuia />
        </section>

        {/* ── Documentación técnica y algoritmos ──────────────────────────── */}
        <section className="acerca-seccion" aria-labelledby="titulo-algoritmos">
          <div className="acerca-seccion__cabeza">
            <h2 id="titulo-algoritmos" className="acerca-seccion__titulo">
              Detalles técnicos
            </h2>
            <p className="acerca-seccion__bajada">
              Descubre cómo funciona DreemGO: cómo selecciona los lugares turísticos, organiza los traslados,
              tiene en cuenta la altura y el clima, calcula los costos y utiliza fuentes de datos abiertos.
            </p>
          </div>

          <div className="acerca-acordeones">
            {/* 1. Zonas y MINCETUR */}
            <details className="acerca-acordeon" name="detalles-tecnicos" open onToggle={alCambiarAcordeon}>
              <summary>
                <span>1. Cómo se seleccionan y priorizan los lugares</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  DreemGO utiliza el Inventario Nacional de Recursos Turísticos de MINCETUR como fuente
                  principal para elegir los lugares que recomienda. Cada atractivo incluye un enlace a su
                  ficha oficial y se clasifica según la importancia que le asigna el ministerio, en una escala
                  del 1 al 4.
                </p>
                <ul>
                  <li>
                    <strong>Jerarquía 4 (Internacional):</strong> Lugares de gran valor turístico que pueden
                    atraer visitantes de todo el mundo, como Machupicchu, las Líneas de Nasca, el lago
                    Titicaca y el cañón del Colca.
                  </li>
                  <li>
                    <strong>Jerarquía 3 (Nacional):</strong> Lugares importantes para el turismo dentro y
                    fuera del país, como la fortaleza de Kuélap, el Parque Nacional Huascarán y la Reserva de
                    Paracas.
                  </li>
                  <li>
                    <strong>Jerarquías 1 y 2 (Regional y local):</strong> Atractivos que destacan por su
                    importancia para una región, localidad o comunidad.
                  </li>
                </ul>
                <p>
                  <strong>¿Cómo los prioriza DreemGO?</strong> Los lugares de jerarquía 3 y 4 se marcan como
                  imperdibles y reciben mayor prioridad al armar el itinerario. Si la ficha oficial no incluye
                  información sobre el precio de entrada o la jerarquía, el sistema lo indica en lugar de
                  inventar un dato.
                </p>
              </div>
            </details>

            {/* 2. Traslados: Bus nocturno vs Avión */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>2. Cómo se organizan los traslados</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  DreemGO tiene en cuenta la distancia entre el punto de partida y el destino para elegir la
                  opción de transporte más conveniente y aprovechar mejor los días de viaje.
                </p>
                <ul>
                  <li>
                    <strong>Menos de 7 horas (distancia corta):</strong> Se propone viajar por carretera
                    durante la mañana del primer día. Si el destino está muy cerca, también se puede organizar
                    una visita de ida y vuelta en el mismo día.
                  </li>
                  <li>
                    <strong>Entre 7 y 16 horas (distancia media):</strong> Se propone viajar en bus nocturno,
                    saliendo la noche anterior al primer día, alrededor de las 9:00 p. m., para llegar
                    aproximadamente a las 6:00 a. m. El regreso se programa de noche el último día. Así, se
                    pueden aprovechar mejor los días de turismo y reducir el gasto en dos noches de hotel.
                  </li>
                  <li>
                    <strong>Más de 16 horas (distancia larga):</strong> Se considera un vuelo comercial,
                    directo o con escala, para evitar pasar varios días en carretera. Si se activa la opción
                    «Solo por tierra», se mantiene el viaje terrestre.
                  </li>
                </ul>
              </div>
            </details>

            {/* 3. Protocolo de Altura CDC */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>3. Recomendaciones para viajar a zonas de altura</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  Llegar a una zona de gran altura requiere tiempo para que el cuerpo se adapte. Por eso,
                  cuando el viajero llega desde una zona de menor altitud y va a dormir a 2.500 metros o más,
                  DreemGO aplica recomendaciones basadas en el{" "}
                  <EnlaceExterno href={CDC_ALTURA}>Yellow Book de los CDC de Estados Unidos</EnlaceExterno>.
                </p>
                <p>Durante los primeros días, el itinerario contempla estas medidas:</p>
                <ul>
                  <li>
                    El inicio de las actividades se retrasa hasta las 9:00 a. m. después de un viaje nocturno,
                    para permitir un tiempo de descanso.
                  </li>
                  <li>
                    Durante las primeras 48 horas, se priorizan las visitas tranquilas y se limita la
                    actividad a medio día como máximo.
                  </li>
                  <li>
                    Se evitan lugares situados a más de 500 metros por encima de la altitud a la que se
                    duerme.
                  </li>
                  <li>
                    No se programan caminatas empinadas ni rutas de trekking exigentes durante el primer día.
                  </li>
                </ul>
                <p>
                  Estas recomendaciones buscan que el viaje sea más llevadero y reducir el riesgo de sufrir
                  molestias relacionadas con la altura.
                </p>
              </div>
            </details>

            {/* 4. Actividades nocturnas */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>4. Actividades nocturnas</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  DreemGO propone actividades para las noches que el viajero pasa en el destino, según sus
                  intereses.
                </p>
                <ul>
                  <li>
                    <strong>Si eliges «Vida nocturna»:</strong> Se recomiendan bares, pubs, discotecas,
                    karaokes y peñas ubicados a un máximo de 25 minutos a pie del alojamiento. La información
                    se obtiene de OpenStreetMap y Overture Maps, una iniciativa respaldada por organizaciones
                    como Meta y Microsoft. Cada lugar incluye un enlace a su mapa para consultar sus horarios
                    y verificar la información.
                  </li>
                  <li>
                    <strong>Si eliges «Naturaleza» o no seleccionas un interés específico:</strong> Se
                    proponen actividades de observación de estrellas y astroturismo. Para ello, se utilizan
                    datos del satélite VIIRS, que permiten evaluar la contaminación lumínica, y del satélite
                    GOES-16, de la NOAA, para analizar la nubosidad de los últimos tres años. El sistema
                    también busca una noche con poca luz lunar para favorecer la observación del cielo.
                  </li>
                </ul>
              </div>
            </details>

            {/* 5. Clima: 10 años */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>5. Clima y lluvias de los últimos 10 años</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  Para cada mes, DreemGO presenta una recomendación sobre la época para viajar: buen mes, con
                  advertencia o desaconsejado.
                </p>
                <p>
                  Esta recomendación se basa en los registros históricos de precipitaciones y humedad de los
                  modelos ERA5 y ERA5-Land de Copernicus, consultados a través de Open-Meteo.
                </p>
                <p>
                  Es importante tener en cuenta que se trata de una evaluación del clima histórico, no de un
                  pronóstico diario. Su objetivo es ayudarte a elegir una época del año que, según los datos
                  disponibles, resulte más conveniente para visitar cada región del Perú.
                </p>
              </div>
            </details>

            {/* 6. Banda de costo */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>6. Cómo se calculan los costos</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  DreemGO presenta un rango estimado de gasto por persona, con un costo mínimo y uno máximo.
                  La estimación considera los siguientes conceptos:
                </p>
                <ul>
                  <li>Transporte terrestre o pasajes aéreos de ida y vuelta.</li>
                  <li>
                    Alojamiento económico en el destino. Las noches que se pasan viajando en bus nocturno no
                    se cuentan como noches de hotel.
                  </li>
                  <li>Alimentación diaria, tomando como referencia almuerzos y cenas habituales.</li>
                  <li>
                    Entradas a los atractivos y tarifas oficiales publicadas en el inventario de MINCETUR.
                  </li>
                </ul>
                <p>
                  Los montos son referenciales y pueden variar según la temporada, los precios vigentes y las
                  decisiones de cada viajero.
                </p>
              </div>
            </details>

            {/* 7. Fiestas y eventos */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>7. Fiestas patronales y eventos publicados</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  El calendario de DreemGO reúne festividades tradicionales registradas en el inventario de
                  MINCETUR y eventos culturales publicados por municipalidades u oficinas de turismo de cada
                  destino.
                </p>
                <p>
                  Cuando hay un evento publicado durante las fechas del viaje, este puede incorporarse al
                  itinerario. Sin embargo, los eventos no cambian el orden de los destinos recomendados, ya
                  que las recomendaciones se basan en los criterios del sistema y no en acuerdos comerciales.
                </p>
                <p>
                  <Enlace href={enlaces.publicar()} className="boton boton--secundario">
                    <Icono nombre="calendario" tamano={16} />
                    Publicar un evento en DreemGO
                  </Enlace>
                </p>
              </div>
            </details>

            {/* 8. Privacidad */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>8. Privacidad</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  No necesitas crear una cuenta para utilizar DreemGO. La información de tu consulta se
                  incluye en el enlace de la página, por lo que puedes compartir la URL para mostrar el viaje
                  completo.
                </p>
                <p>
                  Los viajes que guardas se almacenan únicamente en el almacenamiento local de tu navegador
                  (localStorage). De esta manera, tus preferencias y viajes guardados no necesitan almacenarse
                  en un servidor.
                </p>
              </div>
            </details>

            {/* 9. Límites */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>9. Limitaciones actuales</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  DreemGO todavía tiene algunas limitaciones que debes tener en cuenta al planificar tu viaje:
                </p>
                <ul>
                  <li>
                    Cada itinerario se concentra en una sola zona geográfica. La posibilidad de combinar
                    varias zonas está en desarrollo.
                  </li>
                  <li>
                    No consulta la disponibilidad de buses, vuelos o entradas en tiempo real, ni vende
                    pasajes. Para organizar los traslados, utiliza horarios y opciones habituales.
                  </li>
                  <li>
                    Si una visita se prolonga más de lo previsto antes del almuerzo, la hora de la comida se
                    ajustará al momento en que termine.
                  </li>
                  <li>
                    No siempre puede detectar si un establecimiento nocturno está cerrado temporalmente o en
                    remodelación. Por eso, incluye un enlace al mapa del lugar para que puedas verificar la
                    información antes de visitarlo.
                  </li>
                </ul>
              </div>
            </details>

            {/* 10. Fuentes y licencias */}
            <details className="acerca-acordeon" name="detalles-tecnicos" onToggle={alCambiarAcordeon}>
              <summary>
                <span>10. Fuentes de datos y licencias</span>
                <Icono nombre="abajo" tamano={16} />
              </summary>
              <div className="acerca-acordeon__contenido">
                <p>
                  DreemGO utiliza distintas fuentes de datos abiertos para organizar los viajes y mostrar
                  información sobre los destinos.
                </p>
                <ul>
                  <li>
                    <strong>Lugares turísticos:</strong> Inventario Nacional de Recursos Turísticos de
                    MINCETUR, bajo la licencia ODC-BY 1.0.
                  </li>
                  <li>
                    <strong>Clima y lluvias históricas:</strong> Open-Meteo, con datos de los modelos ERA5 y
                    ERA5-Land de Copernicus, bajo la licencia CC BY 4.0.
                  </li>
                  <li>
                    <strong>Carreteras, rutas de tren, transporte en bote y alojamientos:</strong>{" "}
                    OpenStreetMap, bajo la licencia ODbL 1.0.
                  </li>
                  <li>
                    <strong>Lugares para comer y salir por la noche:</strong> Overture Maps Foundation, con
                    datos de organizaciones como Meta y Microsoft, bajo la licencia CDLA Permissive 2.0, y
                    OpenStreetMap.
                  </li>
                  <li>
                    <strong>Iluminación nocturna e imágenes satelitales:</strong> VIIRS, con información de
                    Colorado School of Mines y el Banco Mundial, y GOES-16, de la NOAA.
                  </li>
                  <li>
                    <strong>Datos de elevación del terreno:</strong> Terrain Tiles de AWS, con información de
                    SRTM y GMTED2010 de USGS.
                  </li>
                  <li>
                    <strong>Mapas base:</strong> OpenFreeMap, con estilos de OpenMapTiles y datos de
                    OpenStreetMap.
                  </li>
                  <li>
                    <strong>Fotografía de portada:</strong> Wikimedia Commons, con imágenes bajo licencias CC
                    BY-SA o de dominio público.
                  </li>
                </ul>
              </div>
            </details>
          </div>
        </section>

        {/* ── Créditos del equipo y CTA ──────────────────────────────────── */}
        <section className="acerca-pie-seccion">
          <h2>Quién lo hace</h2>
          <p>
            Alejandro's Team, para el curso DS3022 Desarrollo de Producto de Datos de la Universidad de
            Ingeniería y Tecnología (UTEC), ciclo 2026-2.
          </p>
          <p>
            El código fuente, los datos procesados y los registros de decisiones de arquitectura están
            disponibles en{" "}
            <EnlaceExterno href={REPOSITORIO}>el repositorio del proyecto en GitHub</EnlaceExterno> con
            licencia MIT.
          </p>
          {opciones.datos && (
            <p className="procedencia">
              Datos {opciones.datos.version_datos} · Contrato {opciones.datos.version_contrato}
            </p>
          )}

          <div className="acerca-cta">
            <Enlace href={enlaces.inicio()} className="boton boton--primario boton--grande">
              Armar un viaje ahora
            </Enlace>
          </div>
        </section>
      </div>
    </>
  );
}
