// Pantalla completa de Blog viajero, inspirada en ¿Y tú qué planes?
// Incluye «Lo más reciente», filtros por categoría, listado detallado de notas y vista de lectura completa.

import { useState } from "react";
import { ARTICULOS_BLOG, type ArticuloBlog, type CategoriaBlog } from "../datos/blog";
import { useTitulo } from "../estado/titulo";
import { urlDeFoto } from "../fotos";
import { Enlace } from "../piezas/Enlace";
import { CreditoDeFoto } from "../piezas/Foto";
import { Icono } from "../piezas/Icono";
import { enlaces } from "../ruta";

const CATEGORIAS: { id: CategoriaBlog | "todos"; etiqueta: string }[] = [
  { id: "todos", etiqueta: "Todos" },
  { id: "experiencia", etiqueta: "Experiencia" },
  { id: "gastronomia", etiqueta: "Gastronomía" },
  { id: "festividades", etiqueta: "Festividades" },
  { id: "viajes con propósito", etiqueta: "Viajes con propósito" },
  { id: "artesanías", etiqueta: "Artesanías" },
  { id: "naturaleza", etiqueta: "Naturaleza" },
  { id: "aventura", etiqueta: "Aventura" },
];

interface Props {
  slug: string | null;
}

export function PaginaBlog({ slug }: Props) {
  const [categoria, setCategoria] = useState<CategoriaBlog | "todos">("todos");
  const [busqueda, setBusqueda] = useState("");

  const articuloAbierto = slug ? ARTICULOS_BLOG.find((a) => a.slug === slug) : null;
  useTitulo(articuloAbierto ? articuloAbierto.titulo : "Blog viajero");

  // Si hay un artículo abierto por URL, mostramos la vista de lectura completa
  if (articuloAbierto) {
    return (
      <article className="blog-articulo-vista">
        <div className="blog-articulo-vista__cabeza">
          <Enlace href={enlaces.blog()} className="boton boton--secundario blog-articulo-vista__volver">
            <Icono nombre="atras" tamano={18} /> Volver al blog
          </Enlace>

          <div className="blog-articulo-vista__metas">
            <span className="blog-tag blog-tag--destacado">{articuloAbierto.categoria}</span>
            <span className="blog-articulo-vista__fecha">
              <Icono nombre="calendario" tamano={14} /> {articuloAbierto.fecha}
            </span>
            <span className="blog-articulo-vista__tiempo">
              <Icono nombre="reloj" tamano={14} /> {articuloAbierto.tiempoLectura}
            </span>
            <span className="blog-articulo-vista__lugar">
              <Icono nombre="pin" tamano={14} /> {articuloAbierto.lugar}
            </span>
          </div>

          <h1 tabIndex={-1} className="blog-articulo-vista__titulo">
            {articuloAbierto.titulo}
          </h1>
          <p className="blog-articulo-vista__extracto">{articuloAbierto.extracto}</p>
        </div>

        <figure className="blog-articulo-vista__portada">
          <img
            src={urlDeFoto(articuloAbierto.foto, 1280)}
            alt={articuloAbierto.titulo}
            className="blog-articulo-vista__img"
          />
          <figcaption className="blog-articulo-vista__pie-foto">
            <CreditoDeFoto foto={articuloAbierto.foto} />
          </figcaption>
        </figure>

        <div className="blog-articulo-vista__cuerpo">
          <div className="blog-articulo-vista__parrafos">
            {articuloAbierto.parrafos.map((p) => (
              <p key={p.slice(0, 30)}>{p}</p>
            ))}
          </div>

          {articuloAbierto.imperdibles.length > 0 && (
            <div className="blog-articulo-vista__seccion-bloque">
              <h2>Lugares y paradas imperdibles</h2>
              <ul className="blog-lista-puntos">
                {articuloAbierto.imperdibles.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {articuloAbierto.consejos.length > 0 && (
            <div className="blog-articulo-vista__seccion-bloque">
              <h2>Consejos para tu visita</h2>
              <ul className="blog-lista-puntos">
                {articuloAbierto.consejos.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* CTA directo al planificador */}
          <div className="blog-articulo-cta">
            <div className="blog-articulo-cta__texto">
              <h3>¿Te animas a conocer {articuloAbierto.lugar}?</h3>
              <p>
                DreemGO planifica tu itinerario personalizado con opciones de viaje, transporte y paradas
                oficiales de MINCETUR.
              </p>
            </div>
            <Enlace href={enlaces.planear()} className="boton boton--primario boton--grande">
              <Icono nombre="mapa" tamano={20} />
              Planear viaje a este destino
            </Enlace>
          </div>
        </div>
      </article>
    );
  }

  // Vista principal del catálogo del blog
  const masRecientes = ARTICULOS_BLOG.slice(0, 4);

  const filtrados = ARTICULOS_BLOG.filter((art) => {
    const coincideCat = categoria === "todos" || art.categoria === categoria;
    const coincideTexto =
      busqueda === "" ||
      art.titulo.toLowerCase().includes(busqueda.toLowerCase()) ||
      art.extracto.toLowerCase().includes(busqueda.toLowerCase()) ||
      art.lugar.toLowerCase().includes(busqueda.toLowerCase());
    return coincideCat && coincideTexto;
  });

  return (
    <div className="pagina-blog">
      {/* ── Encabezado principal del Blog ──────────────────────────────── */}
      <header className="blog-hero">
        <span className="blog-hero__icono" aria-hidden="true">
          <Icono nombre="avion" tamano={42} />
        </span>
        <h1 tabIndex={-1} className="blog-hero__titulo">
          Blog viajero
        </h1>
        <p className="blog-hero__bajada">
          ¡Asegúrate de no perderte de nada en tu próximo viaje por el Perú! Rutas, tradiciones, gastronomía y
          guías de viaje.
        </p>
      </header>

      {/* ── Sección: Lo más reciente (Carrusel de 4 tarjetas) ──────────── */}
      <section className="blog-seccion blog-seccion--reciente" aria-labelledby="titulo-lo-mas-reciente">
        <div className="blog-seccion__cabeza-simple">
          <h2 id="titulo-lo-mas-reciente" className="blog-seccion__titulo-simple">
            Lo más reciente
          </h2>
        </div>

        <section className="blog-recientes-grid" aria-label="Artículos más recientes">
          {masRecientes.map((art: ArticuloBlog) => (
            <article key={art.id} className="blog-reciente-tarjeta">
              <div className="blog-reciente-tarjeta__media">
                <img
                  src={urlDeFoto(art.foto, 500)}
                  alt={art.titulo}
                  className="blog-reciente-tarjeta__img"
                  loading="lazy"
                  decoding="async"
                />
              </div>
              <div className="blog-reciente-tarjeta__cuerpo">
                <h3 className="blog-reciente-tarjeta__titulo" title={art.titulo}>
                  {art.titulo}
                </h3>
                <div className="blog-reciente-tarjeta__pie">
                  <span className="blog-reciente-tarjeta__lugar">
                    <Icono nombre="pin" tamano={14} />
                    {art.lugar}
                  </span>
                  <Enlace
                    href={enlaces.blog(art.slug)}
                    className="blog-reciente-tarjeta__enlace"
                    aria-label={`Ver artículo: ${art.titulo}`}
                  >
                    <Icono nombre="flecha" tamano={16} />
                  </Enlace>
                </div>
              </div>
            </article>
          ))}
        </section>
      </section>

      {/* ── Filtros por categoría (Píldoras) ─────────────────────────────── */}
      <section className="blog-filtros-seccion" aria-label="Filtrar notas por categoría">
        <div className="blog-filtros" role="tablist">
          {CATEGORIAS.map((cat) => (
            <button
              key={cat.id}
              type="button"
              role="tab"
              aria-selected={categoria === cat.id}
              className={`blog-filtro-pill${categoria === cat.id ? " blog-filtro-pill--activo" : ""}`}
              onClick={() => setCategoria(cat.id)}
            >
              {cat.etiqueta}
            </button>
          ))}
        </div>

        {/* Buscador opcional */}
        <div className="blog-buscador">
          <Icono nombre="lupa" tamano={18} />
          <input
            type="search"
            placeholder="Buscar notas, lugares o temas..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            aria-label="Buscar en el blog"
            className="blog-buscador__input"
          />
          {busqueda && (
            <button
              type="button"
              className="blog-buscador__limpiar"
              onClick={() => setBusqueda("")}
              aria-label="Limpiar búsqueda"
            >
              ×
            </button>
          )}
        </div>
      </section>

      {/* ── Listado general de artículos (Feed estilo ¿Y tú qué planes?) ─ */}
      <section className="blog-feed" aria-label="Listado de artículos del blog">
        <div className="blog-feed__lista">
          {filtrados.length === 0 ? (
            <div className="blog-feed__vacio">
              <p>No se encontraron notas para esta categoría o búsqueda.</p>
              <button
                type="button"
                className="boton boton--secundario"
                onClick={() => {
                  setCategoria("todos");
                  setBusqueda("");
                }}
              >
                Ver todas las notas
              </button>
            </div>
          ) : (
            filtrados.map((art: ArticuloBlog) => (
              <article key={art.id} className="blog-feed-item">
                <div className="blog-feed-item__media">
                  <img
                    src={urlDeFoto(art.foto, 500)}
                    alt={art.titulo}
                    className="blog-feed-item__img"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <div className="blog-feed-item__cuerpo">
                  <div className="blog-feed-item__tags">
                    <span className="blog-tag">{art.categoria}</span>
                  </div>
                  <h2 className="blog-feed-item__titulo">
                    <Enlace href={enlaces.blog(art.slug)}>{art.titulo}</Enlace>
                  </h2>
                  <p className="blog-feed-item__extracto">{art.extracto}</p>
                  <div className="blog-feed-item__pie">
                    <span className="blog-feed-item__lugar">
                      <Icono nombre="pin" tamano={14} />
                      {art.lugar}
                    </span>
                    <span className="blog-feed-item__fecha">{art.fecha}</span>
                    <Enlace
                      href={enlaces.blog(art.slug)}
                      className="blog-feed-item__leer-mas"
                      aria-label={`Leer nota: ${art.titulo}`}
                    >
                      Ver más <Icono nombre="flecha" tamano={14} />
                    </Enlace>
                  </div>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
