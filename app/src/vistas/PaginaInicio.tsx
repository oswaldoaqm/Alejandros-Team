// Pantalla de Inicio: carrusel hero de destinos peruanos, invitación rápida a planear,
// festividades y eventos destacados del mes y notas del blog viajero al estilo ¿Y tú qué planes?

import { useMemo, useState } from "react";
import { consultaNueva } from "../consulta";
import { ARTICULOS_BLOG, type ArticuloBlog } from "../datos/blog";
import { type FestividadMes, obtenerFestividadesVivas } from "../datos/festividades";
import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { urlDeFoto } from "../fotos";
import { CarruselHero } from "../piezas/CarruselHero";
import { Enlace } from "../piezas/Enlace";
import { Hoja } from "../piezas/Hoja";
import { Icono } from "../piezas/Icono";
import { enlaces } from "../ruta";

export function PaginaInicio() {
  const { navegar } = useApp();
  const [festividadAbierta, setFestividadAbierta] = useState<FestividadMes | null>(null);
  useTitulo(null); // Título base: «DreemGO»

  const elegirDestinoDirecto = (destinoId: number) => {
    navegar(enlaces.resultados(consultaNueva({ destino: destinoId, sorpresa: false }), null, 1));
  };

  const festividades = useMemo(() => obtenerFestividadesVivas(), []);

  const articuloPrincipal =
    ARTICULOS_BLOG.find((a) => a.destacadoEnHome) ?? (ARTICULOS_BLOG[0] as ArticuloBlog);
  const articulosSecundarios = ARTICULOS_BLOG.filter((a) => a.id !== articuloPrincipal.id).slice(0, 3);

  return (
    <div className="pagina-inicio">
      {/* El título de la página, para los lectores de pantalla: el carrusel cambia de título a cada rato. */}
      <h1 className="solo-lector">DreemGO: viajes por el Perú</h1>
      {/* ── 1. Carrusel Hero a pantalla completa ──────────────────────────── */}
      <CarruselHero onElegirDestino={elegirDestinoDirecto} />

      {/* ── 2. Banner de acceso al Planificador ───────────────────────────── */}
      <section className="inicio-cta-planear" aria-labelledby="titulo-cta-planear">
        <div className="inicio-cta-planear__caja">
          <div className="inicio-cta-planear__texto">
            <h2 id="titulo-cta-planear" className="inicio-cta-planear__titulo">
              Tu planificador inteligente de viajes
            </h2>
            <p className="inicio-cta-planear__bajada">
              Cuéntanos desde dónde sales, cuántos días tienes y qué te apasiona. DreemGO calcula tres
              itinerarios optimizados con datos oficiales de MINCETUR, protocolo de altura y costos
              transparentes.
            </p>
          </div>
          <div className="inicio-cta-planear__acciones">
            <Enlace href={enlaces.acerca()} className="boton boton--secundario boton--grande">
              <Icono nombre="ayuda" tamano={20} />
              Cómo funciona
            </Enlace>
            <p className="inicio-cta-planear__llamado">¿Qué esperas para explorar?</p>
            <Enlace href={enlaces.planear()} className="boton boton--primario boton--grande">
              <Icono nombre="mapa" tamano={20} />
              Armar mi viaje
            </Enlace>
          </div>
        </div>
      </section>

      {/* ── 3. Apartado de Fiestas: Festividades y eventos del mes ───────── */}
      <section className="inicio-seccion inicio-fiestas" aria-labelledby="titulo-fiestas-mes">
        <div className="inicio-seccion__cabeza">
          <div className="inicio-seccion__icono-adorno" aria-hidden="true">
            <Icono nombre="mascara_festiva" tamano={42} />
          </div>
          <h2 id="titulo-fiestas-mes" className="inicio-seccion__titulo">
            Festividades y eventos del mes
          </h2>
          <p className="inicio-seccion__bajada">
            Celebra las danzas, ferias patronales y tradiciones vivas que llenan de color y música a las
            regiones del Perú.
          </p>
        </div>

        <section className="festividades-grid" aria-label="Festividades destacadas del mes">
          {festividades.map((fest: FestividadMes) => (
            <article key={fest.id} className="festividad-tarjeta">
              <div className="festividad-tarjeta__media">
                <img
                  src={urlDeFoto(fest.foto, 500)}
                  alt={fest.titulo}
                  className="festividad-tarjeta__img"
                  loading="lazy"
                  decoding="async"
                />
                {/* Badge de fecha arriba-izquierda */}
                <div
                  className="festividad-tarjeta__badge-fecha"
                  title={`Fechas: ${fest.diaRango} de ${fest.mesRango}`}
                >
                  <span className="festividad-tarjeta__badge-dias">{fest.diaRango}</span>
                  <span className="festividad-tarjeta__badge-meses">{fest.mesRango}</span>
                </div>
                {/* Badge de categoría abajo-izquierda */}
                <div className="festividad-tarjeta__badge-cat">{fest.categoria}</div>
              </div>

              <div className="festividad-tarjeta__cuerpo">
                <h3 className="festividad-tarjeta__titulo" title={fest.titulo}>
                  {fest.titulo}
                </h3>
                <p className="festividad-tarjeta__extracto">{fest.extracto}</p>
                <div className="festividad-tarjeta__pie">
                  <span className="festividad-tarjeta__lugar">
                    <Icono nombre="pin" tamano={15} />
                    {fest.lugar}
                  </span>
                  <button
                    type="button"
                    className="festividad-tarjeta__enlace festividad-tarjeta__boton-ver"
                    onClick={() => setFestividadAbierta(fest)}
                    aria-haspopup="dialog"
                    aria-label={`Ver más sobre ${fest.titulo}`}
                  >
                    Ver más <Icono nombre="flecha" tamano={14} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </section>

        <div className="inicio-seccion__pie-boton">
          <Enlace href={enlaces.calendario()} className="boton boton--amarillo-ytqp boton--grande">
            Ver todas las festividades <Icono nombre="flecha" tamano={18} />
          </Enlace>
        </div>
      </section>

      {/* ── 4. Apartado de Blog Viajero ──────────────────────────────────── */}
      <section className="inicio-seccion inicio-blog" aria-labelledby="titulo-blog-inicio">
        <div className="inicio-seccion__cabeza">
          <div className="inicio-seccion__icono-adorno" aria-hidden="true">
            <Icono nombre="avion" tamano={38} />
          </div>
          <h2 id="titulo-blog-inicio" className="inicio-seccion__titulo">
            Blog viajero
          </h2>
          <p className="inicio-seccion__bajada">
            ¡Asegúrate de no perderte de nada en tu próximo viaje por el Perú! Consejos prácticos, rutas y
            guías locales.
          </p>
        </div>

        <section className="inicio-blog__layout" aria-label="Notas destacadas del blog viajero">
          {/* Tarjeta principal izquierda */}
          <article className="inicio-blog__destacado">
            <div className="inicio-blog__destacado-media">
              <img
                src={urlDeFoto(articuloPrincipal.foto, 960)}
                alt={articuloPrincipal.titulo}
                className="inicio-blog__destacado-img"
                loading="lazy"
                decoding="async"
              />
              <span className="inicio-blog__cat-tag">{articuloPrincipal.categoria}</span>
            </div>
            <div className="inicio-blog__destacado-cuerpo">
              <h3 className="inicio-blog__destacado-titulo">{articuloPrincipal.titulo}</h3>
              <p className="inicio-blog__destacado-extracto">{articuloPrincipal.extracto}</p>
              <div className="inicio-blog__destacado-pie">
                <span className="inicio-blog__lugar">
                  <Icono nombre="pin" tamano={15} />
                  {articuloPrincipal.lugar}
                </span>
                <Enlace
                  href={enlaces.blog(articuloPrincipal.slug)}
                  className="inicio-blog__enlace"
                  aria-label={`Leer artículo: ${articuloPrincipal.titulo}`}
                >
                  Ver más <Icono nombre="flecha" tamano={14} />
                </Enlace>
              </div>
            </div>
          </article>

          {/* Tarjetas secundarias derechas */}
          <div className="inicio-blog__secundarios">
            {articulosSecundarios.map((art: ArticuloBlog) => (
              <article key={art.id} className="inicio-blog__fila-tarjeta">
                <div className="inicio-blog__fila-media">
                  <img
                    src={urlDeFoto(art.foto, 330)}
                    alt={art.titulo}
                    className="inicio-blog__fila-img"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <div className="inicio-blog__fila-cuerpo">
                  <span className="inicio-blog__fila-cat">{art.categoria}</span>
                  <h3 className="inicio-blog__fila-titulo" title={art.titulo}>
                    {art.titulo}
                  </h3>
                  <p className="inicio-blog__fila-extracto">{art.extracto}</p>
                  <div className="inicio-blog__fila-pie">
                    <span className="inicio-blog__lugar">
                      <Icono nombre="pin" tamano={14} />
                      {art.lugar}
                    </span>
                    <Enlace
                      href={enlaces.blog(art.slug)}
                      className="inicio-blog__enlace"
                      aria-label={`Leer artículo: ${art.titulo}`}
                    >
                      Ver más <Icono nombre="flecha" tamano={13} />
                    </Enlace>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <div className="inicio-seccion__pie-boton">
          <Enlace href={enlaces.blog()} className="boton boton--vino-ytqp boton--grande">
            Ver todas las notas <Icono nombre="flecha" tamano={18} />
          </Enlace>
        </div>
      </section>

      {/* ── Hoja / Modal de Detalle de Festividad ──────────────────────── */}
      <Hoja
        abierta={festividadAbierta !== null}
        alCerrar={() => setFestividadAbierta(null)}
        titulo={festividadAbierta?.titulo ?? ""}
        pie={
          festividadAbierta ? (
            <div className="hoja-festividad__pie-acciones">
              <Enlace
                href={enlaces.planear(
                  consultaNueva({ destino: festividadAbierta.destinoId, sorpresa: false }),
                )}
                className="boton boton--primario boton--grande boton--ancho"
                onClick={() => setFestividadAbierta(null)}
              >
                <Icono nombre="mapa" tamano={20} />
                Planear viaje a {festividadAbierta.destinoNombre}
              </Enlace>
            </div>
          ) : null
        }
      >
        {festividadAbierta ? (
          <div className="hoja-festividad">
            <div className="hoja-festividad__portada">
              <img
                src={urlDeFoto(festividadAbierta.foto, 960)}
                alt={festividadAbierta.titulo}
                className="hoja-festividad__img"
                loading="eager"
                decoding="async"
              />
              <div className="hoja-festividad__badge-fecha">
                <span className="hoja-festividad__badge-dias">{festividadAbierta.diaRango}</span>
                <span className="hoja-festividad__badge-meses">{festividadAbierta.mesRango}</span>
              </div>
              <div className="hoja-festividad__badge-cat">{festividadAbierta.categoria}</div>
            </div>

            <div className="hoja-festividad__metas">
              <span className="hoja-festividad__meta">
                <Icono nombre="pin" tamano={16} />
                <strong>{festividadAbierta.lugar}</strong> ({festividadAbierta.region})
              </span>
              <span className="hoja-festividad__meta">
                <Icono nombre="calendario" tamano={16} />
                {festividadAbierta.fechasTexto}
              </span>
            </div>

            {/* Texto de la vista previa para mantener continuidad */}
            <p className="hoja-festividad__extracto">{festividadAbierta.extracto}</p>

            <p className="hoja-festividad__descripcion">{festividadAbierta.descripcionDetallada}</p>

            {festividadAbierta.actividades && festividadAbierta.actividades.length > 0 ? (
              <div className="hoja-festividad__seccion">
                <h3 className="hoja-festividad__subtitulo">Actividades destacadas</h3>
                <ul className="hoja-festividad__lista">
                  {festividadAbierta.actividades.map((act) => (
                    <li key={act}>{act}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div className="hoja-festividad__nota-fuente">
              <Icono nombre="info" tamano={16} />
              <span>Información oficial recopilada del inventario y calendarios de MINCETUR.</span>
            </div>
          </div>
        ) : null}
      </Hoja>
    </div>
  );
}
