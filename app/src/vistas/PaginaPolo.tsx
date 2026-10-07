// La zona de un viaje: todo lo que hay para ver alrededor de donde se duerme, cómo es su clima
// mes a mes y qué fiestas vienen. Se llega desde un viaje («Ver todos los lugares de la zona») y su
// enlace se puede compartir. Sale de GET /v1/polos/{id}.

import { useMemo, useState } from "react";
import type { PoloDetalle, Recurso } from "../api/tipos";
import type { Consulta } from "../consulta";
import { useFotos } from "../estado/fotos";
import { usePedido } from "../estado/pedido";
import { useTitulo } from "../estado/titulo";
import { lista, metros, plural, rangosDeMeses } from "../formato";
import { type FotoDe, type Fotos, fotoDeLaZona, urlDeFoto } from "../fotos";
import { ClimaAnual } from "../piezas/ClimaAnual";
import { type Dato, DatosClave } from "../piezas/DatosClave";
import { Enlace } from "../piezas/Enlace";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { CreditoDeFoto, Foto } from "../piezas/Foto";
import { Icono } from "../piezas/Icono";
import { ListaEventos } from "../piezas/Listas";
import { claseDeRecurso, esImperdible, HojaDeRecurso, Imperdible } from "../piezas/Recurso";
import { enlaces } from "../ruta";
import { nombreDelViaje } from "../textos";

/** Cuántos lugares se ven antes de «Ver todos»: los más importantes. */
const PRIMEROS = 8;

function datosDeLaZona(detalle: PoloDetalle): Dato[] {
  const { polo, recursos, eventos } = detalle;
  const estrellas = recursos.filter(esImperdible).length;
  const datos: Dato[] = [
    {
      etiqueta: "Lugares",
      icono: "pin",
      valor: String(recursos.length),
      nota: "para visitar",
    },
  ];
  if (estrellas > 0) {
    datos.push({
      etiqueta: "Imperdibles",
      icono: "estrella",
      valor: String(estrellas),
      nota: estrellas === 1 ? "imperdible" : "imperdibles",
      imperdible: true,
    });
  }
  if (polo.base.altitud_m != null) {
    datos.push({
      etiqueta: "Altura",
      icono: "montana",
      valor: metros(polo.base.altitud_m),
      nota: "donde duermes",
    });
  }
  datos.push({
    etiqueta: "Fiestas",
    icono: "fiestas",
    valor: String(eventos.length),
    nota: "en los próximos doce meses",
  });
  return datos;
}

/** «Buen clima de abril a noviembre», o null si ningún mes es seco. */
function resumenDelClima(detalle: PoloDetalle): string | null {
  const buenos = detalle.clima.filter((m) => m.veredicto === "viable").map((m) => m.mes);
  if (buenos.length === 0) return null;
  const cuando = rangosDeMeses(buenos);
  return cuando === "todo el año"
    ? "Buen clima todo el año."
    : `Buen clima ${cuando.startsWith("de ") ? "" : "en "}${cuando}.`;
}

function FilaDeLugar({
  recurso,
  fotos,
  abrir,
}: {
  recurso: Recurso;
  fotos: Fotos | null;
  abrir: () => void;
}) {
  const foto = fotos?.lugares[recurso.codigo];
  const [sinFoto, ponerSinFoto] = useState(false);
  return (
    <li>
      <button type="button" className="zona-lugar" onClick={abrir} aria-haspopup="dialog">
        <span className="zona-lugar__foto" aria-hidden="true">
          <Icono nombre="pin" tamano={20} />
          {foto && !sinFoto ? (
            <img
              src={urlDeFoto(foto, 330)}
              alt=""
              width={foto.ancho}
              height={foto.alto}
              loading="lazy"
              decoding="async"
              onError={() => ponerSinFoto(true)}
            />
          ) : null}
        </span>
        <span className="zona-lugar__texto">
          <span className="zona-lugar__nombre">{recurso.nombre}</span>{" "}
          <span className="zona-lugar__meta">
            {esImperdible(recurso) ? (
              <>
                <Imperdible tamano={14} />{" "}
              </>
            ) : null}
            <span>{claseDeRecurso(recurso)}</span>
          </span>
        </span>
        <Icono nombre="flecha" tamano={18} />
      </button>
    </li>
  );
}

interface PropsDeZona {
  detalle: PoloDetalle;
  fotos: Fotos | null;
  /** El mes del viaje, si se llegó desde uno: el clima se abre en él. */
  mes: number | null;
}

function Zona({ detalle, fotos, mes }: PropsDeZona) {
  const { polo, recursos, clima, eventos } = detalle;
  const [todos, verTodos] = useState(false);
  const [abierto, abrir] = useState<string | null>(null);
  const visibles = todos ? recursos : recursos.slice(0, PRIMEROS);
  const recursoAbierto = recursos.find((r) => r.codigo === abierto) ?? null;
  const resumen = resumenDelClima(detalle);

  return (
    <>
      <section className="zona__lugares" aria-labelledby="zona-lugares">
        <h2 id="zona-lugares" className="viaje__titular">
          Qué hay para ver
        </h2>
        <p className="zona__bajada">
          {plural(recursos.length, "lugar", "lugares")}, de los más importantes a los menos conocidos.
        </p>
        <ul className="zona-lugares">
          {visibles.map((r) => (
            <FilaDeLugar key={r.codigo} recurso={r} fotos={fotos} abrir={() => abrir(r.codigo)} />
          ))}
        </ul>
        {recursos.length > PRIMEROS ? (
          <button
            type="button"
            className="boton boton--secundario zona__mas"
            aria-expanded={todos}
            onClick={() => verTodos(!todos)}
          >
            {todos ? "Ver menos" : `Ver los ${recursos.length} lugares`}
          </button>
        ) : null}
      </section>

      <div className="zona__lado">
        <section aria-labelledby="zona-clima">
          <h2 id="zona-clima" className="viaje__titular">
            El clima, mes a mes
          </h2>
          {resumen ? <p className="zona__bajada">{resumen}</p> : null}
          <ClimaAnual clima={clima} inicial={mes ?? new Date().getMonth() + 1} />
        </section>

        <section aria-labelledby="zona-fiestas">
          <h2 id="zona-fiestas" className="viaje__titular">
            Fiestas de los próximos meses
          </h2>
          <ListaEventos
            eventos={eventos}
            limite={5}
            vacio="No hay fiestas registradas en esta zona para los próximos doce meses."
          />
        </section>
      </div>

      <footer className="letra-chica">
        <h2 className="letra-chica__titulo">Sobre estos datos</h2>
        {polo.recursos > recursos.length ? (
          <p>
            El inventario oficial tiene {plural(polo.recursos, "lugar", "lugares")} en esta zona; aquí van los{" "}
            {recursos.length} que se pueden visitar.
          </p>
        ) : null}
        <p>
          La importancia de cada lugar es la jerarquía que le da MINCETUR, de 1 a 4. Desde 3, son imperdibles:
          de los lugares más importantes del país.
        </p>
        {polo.fuera_del_circuito ? (
          <p>Está fuera del circuito de Lima y Cusco: ninguno de sus lugares queda en esas dos regiones.</p>
        ) : null}
        {fotos ? (
          <p>Las fotos son de Wikimedia Commons: cada una lleva el nombre de su autor y su licencia.</p>
        ) : null}
        <ul className="letra-chica__fuentes">
          {detalle.atribucion.map((linea) => (
            <li key={linea}>{linea}</li>
          ))}
        </ul>
        <p>Datos {detalle.version_datos}.</p>
      </footer>

      <HojaDeRecurso
        recurso={recursoAbierto}
        foto={recursoAbierto ? (fotos?.lugares[recursoAbierto.codigo] ?? null) : null}
        alCerrar={() => abrir(null)}
      />
    </>
  );
}

function Portada({ foto, alFallar }: { foto: FotoDe; alFallar: () => void }) {
  return (
    <div className="portada__arte portada__arte--foto">
      <Foto
        foto={foto.foto}
        alt={foto.de}
        sizes="(min-width: 960px) 520px, calc(100vw - 40px)"
        principal
        credito={null}
        alFallar={alFallar}
        className="portada__foto"
      />
      <p className="portada__credito">
        <span className="portada__lugar">{foto.de}</span>
        <span>
          <CreditoDeFoto foto={foto.foto} />
        </span>
      </p>
    </div>
  );
}

export function PaginaPolo({ id, consulta }: { id: number; consulta: Consulta | null }) {
  const pedido = usePedido<PoloDetalle>(`/v1/polos/${id}`);
  const fotos = useFotos();
  const [sinFoto, ponerSinFoto] = useState(false);
  const detalle = pedido.datos;
  const nombre = detalle ? nombreDelViaje(detalle.polo.nombre) : null;
  useTitulo(nombre?.titulo ?? "La zona");
  const foto = useMemo(
    () => (detalle && fotos && !sinFoto ? fotoDeLaZona(detalle.polo, detalle.recursos, fotos) : null),
    [detalle, fotos, sinFoto],
  );

  return (
    <article className="viaje zona">
      <div className="zona__cuerpo">
        {/* El título es el mismo elemento antes y después de cargar: el foco que llega a él no se pierde. */}
        <header className={`portada${foto ? "" : " portada--sin-arte"}`}>
          {foto ? <Portada foto={foto} alFallar={() => ponerSinFoto(true)} /> : null}
          <div className="portada__barra">
            <Enlace
              href={consulta ? enlaces.resultados(consulta) : enlaces.inicio()}
              volver
              className="boton boton--flotante portada__volver"
            >
              <Icono nombre="atras" tamano={20} />
              <span className="boton__texto">{consulta ? "Tus viajes" : "Inicio"}</span>
            </Enlace>
          </div>
          <div className="portada__texto">
            <h1 tabIndex={-1} className="portada__titulo">
              {nombre?.titulo ?? "La zona"}
            </h1>
            {nombre?.subtitulo ? <p className="portada__sub">{nombre.subtitulo}</p> : null}
            {detalle ? (
              <>
                <ul className="portada__datos">
                  <li>
                    <Icono nombre="pin" />
                    {lista(detalle.polo.regiones)}
                  </li>
                  <li>
                    <Icono nombre="cama" />
                    Duermes en {detalle.polo.base.nombre}
                  </li>
                  {detalle.polo.fuera_del_circuito ? (
                    <li>
                      <Icono nombre="aventura" />
                      Fuera del circuito
                    </li>
                  ) : null}
                </ul>
                <DatosClave datos={datosDeLaZona(detalle)} />
              </>
            ) : null}
          </div>
        </header>

        {detalle ? (
          <Zona detalle={detalle} fotos={fotos} mes={consulta?.mes ?? null} />
        ) : pedido.error ? (
          <ErrorVista error={pedido.error} reintentar={pedido.reintentar} />
        ) : (
          <Cargando texto="Cargando la zona…" />
        )}
      </div>
    </article>
  );
}
