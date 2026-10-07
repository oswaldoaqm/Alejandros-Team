// La pantalla de un viaje. Arriba, lo que decide: la flor del viaje, su nombre y cuatro datos
// (cuánto cuesta, cuánto se tarda en llegar, el clima del mes y la altura). Después, por qué vale
// la pena y lo que hay que saber antes de ir; el mapa y el plan, de a un día; el costo, el clima y
// las fiestas; y al final, de dónde sale todo. En pantalla ancha el mapa queda fijo a la derecha.

import { type ReactNode, useMemo, useRef, useState } from "react";
import type { Aviso, Ruta } from "../api/tipos";
import type { Consulta } from "../consulta";
import { horas, lista, mes, metros, plural, soles } from "../formato";
import { type Fotos, fotoDelViaje } from "../fotos";
import { esExcursion, numerar, puntosDeMapa } from "../itinerario";
import { llevarA } from "../movimiento";
import { enlaces } from "../ruta";
import {
  ALTURA_QUE_SE_SIENTE,
  CLIMA_EN_POCAS_PALABRAS,
  imperdibles,
  lugaresDelViaje,
  nombreDelViaje,
  razonesQueFaltan,
  resumenDeLugares,
} from "../textos";
import { BandaCosto } from "./BandaCosto";
import { type Dato, DatosClave } from "./DatosClave";
import { Enlace } from "./Enlace";
import { DibujoFlor } from "./Flor";
import { CreditoDeFoto, Foto } from "./Foto";
import { Icono, type NombreDeIcono } from "./Icono";
import { HojaDeLugar, Itinerario, type LugarAbierto, PlanParaImprimir, SelectorDeDias } from "./Itinerario";
import { ListaEventos } from "./Listas";
import { Mapa } from "./Mapa";
import { Temporada } from "./Temporada";

interface Props {
  ruta: Ruta;
  /** La lista de fotos; null mientras llega o si no llega: va la flor. */
  fotos: Fotos | null;
  consulta: Consulta;
  version: string | null;
  /** El enlace a los viajes propuestos. */
  volver: string;
  /** El aviso de que el enlace se armó con otros datos, cuando hace falta. */
  aviso?: ReactNode;
  /** Guardar y compartir: van sobre la portada. */
  acciones?: ReactNode;
  atribucion: string[];
  /** «Datos 2026.10.2, contrato 1.2». */
  versiones: string;
}

// ── Los datos que deciden ──────────────────────────────────────────────────────────

function datosClave(ruta: Ruta, excursion: boolean): Dato[] {
  const { costo, traslado, estacionalidad, indicadores } = ruta;
  const medios = traslado.medios ?? [];
  const datos: Dato[] = [
    {
      etiqueta: "Costo",
      icono: "billete",
      valor: soles(costo.p50),
      nota: costo.exceso ? `${soles(costo.exceso)} sobre tu presupuesto` : "por persona",
      aviso: Boolean(costo.exceso),
    },
  ];
  if (traslado.horas != null) {
    datos.push({
      etiqueta: excursion ? "Hasta el primer lugar" : "Viaje de ida",
      icono: medios.includes("tren") ? "tren" : medios.includes("bote") ? "bote" : "bus",
      valor: horas(traslado.horas),
      nota: `desde ${traslado.desde}`,
    });
  }
  datos.push({
    etiqueta: "Clima",
    icono: estacionalidad.veredicto === "viable" ? "sol" : "lluvia",
    valor: CLIMA_EN_POCAS_PALABRAS[estacionalidad.veredicto],
    nota: `en ${mes(estacionalidad.mes)}`,
  });
  const altura = indicadores.altitud_max_m;
  if (altura != null && altura >= ALTURA_QUE_SE_SIENTE) {
    datos.push({ etiqueta: "Altura", icono: "montana", valor: metros(altura), nota: "lo más alto" });
  } else {
    const lugares = lugaresDelViaje(ruta.dias);
    datos.push({
      etiqueta: "Lugares",
      icono: "pin",
      valor: String(lugares),
      nota: lugares === 1 ? "lugar" : "lugares",
    });
  }
  return datos;
}

// ── Por qué, y antes de ir ─────────────────────────────────────────────────────────

function Razones({ ruta }: { ruta: Ruta }) {
  const estrellas = imperdibles(ruta.dias);
  const otras = razonesQueFaltan(ruta.motivos);
  if (estrellas.length === 0 && otras.length === 0) return null;
  return (
    <section className="viaje__bloque" aria-labelledby="titulo-razones">
      <h2 id="titulo-razones" className="viaje__titular">
        Por qué te va a gustar
      </h2>
      <ul className="razones">
        {estrellas.length > 0 ? (
          <li className="razon razon--imperdible">
            <Icono nombre="estrella" relleno />
            <p>
              {estrellas.length === 1 ? (
                <>
                  <strong>{estrellas[0]}</strong>, de los lugares más importantes del país.
                </>
              ) : (
                <>
                  <strong>{plural(estrellas.length, "imperdible", "imperdibles")}</strong>:{" "}
                  {resumenDeLugares(estrellas, 3)}.
                </>
              )}
            </p>
          </li>
        ) : null}
        {otras.map((m) => (
          <li key={m} className="razon">
            <Icono nombre="bien" />
            <p>{m}.</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

const ICONO_DEL_AVISO: Record<Aviso["tipo"], NombreDeIcono> = {
  estacionalidad: "lluvia",
  altitud: "montana",
  aclimatacion: "montana",
  presupuesto: "billete",
  acceso: "bote",
  dias: "reloj",
  datos: "info",
};

function AntesDeIr({ avisos }: { avisos: Aviso[] }) {
  if (avisos.length === 0) return null;
  return (
    <section className="viaje__bloque" aria-labelledby="titulo-antes">
      <h2 id="titulo-antes" className="viaje__titular">
        Antes de ir
      </h2>
      <ul className="antes">
        {avisos.map((a) => (
          <li key={`${a.tipo}-${a.mensaje}`} className={`antes__aviso antes__aviso--${a.nivel}`}>
            <Icono nombre={ICONO_DEL_AVISO[a.tipo]} />
            <p>
              <span className="solo-lector">
                {a.nivel === "advertencia" ? "Importante: " : "Para saber: "}
              </span>
              {a.mensaje}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

// ── La pantalla ────────────────────────────────────────────────────────────────────

export function DetalleRuta({
  ruta,
  fotos,
  consulta,
  version,
  volver,
  aviso,
  acciones,
  atribucion,
  versiones,
}: Props) {
  const { polo, traslado, costo, estacionalidad } = ruta;
  const [dia, ponerDia] = useState<number | null>(null);
  const [abierto, ponerAbierto] = useState<{ dia: number; codigo: string } | null>(null);
  const tituloDelPlan = useRef<HTMLHeadingElement>(null);
  const [sinFoto, ponerSinFoto] = useState(false);
  const portada = useMemo(
    () => (fotos && !sinFoto ? fotoDelViaje(ruta, fotos) : null),
    [fotos, ruta, sinFoto],
  );

  const dias = useMemo(() => numerar(ruta.dias), [ruta.dias]);
  const puntos = useMemo(() => puntosDeMapa(dias), [dias]);
  const excursion = esExcursion(ruta);
  const { nombre, lat, lon } = polo.base;
  const base = useMemo(() => (excursion ? null : { nombre, lat, lon }), [excursion, nombre, lat, lon]);
  const desdeDelDia = excursion ? traslado.desde : polo.base.nombre;
  const { titulo, subtitulo } = nombreDelViaje(polo.nombre);
  const eventos = ruta.eventos ?? [];
  const avisos = ruta.avisos ?? [];
  const avisosDelViaje = avisos
    .filter((a) => a.tipo !== "datos")
    .sort((a, b) => Number(b.nivel === "advertencia") - Number(a.nivel === "advertencia"));
  const avisosDeLosDatos = avisos.filter((a) => a.tipo === "datos");

  const elegirDia = (nuevo: number | null) => {
    ponerDia(nuevo);
    // Si el comienzo del plan quedó arriba, fuera de la vista, se vuelve a él: el día nuevo se lee
    // desde su primer lugar, con el mapa a la vista.
    const titular = tituloDelPlan.current;
    if (titular && titular.getBoundingClientRect().top < 0) llevarA(titular, "start");
  };

  const lugar = useMemo<LugarAbierto | null>(() => {
    if (!abierto) return null;
    const delDia = dias.find((d) => d.dia.numero === abierto.dia);
    const indice = delDia ? delDia.paradas.findIndex((p) => p.parada.recurso.codigo === abierto.codigo) : -1;
    const encontrada = delDia?.paradas[indice];
    if (!encontrada) return null;
    const anterior = delDia?.paradas[indice - 1];
    return {
      parada: encontrada.parada,
      numero: encontrada.numero,
      dia: abierto.dia,
      desde: anterior ? anterior.parada.recurso.nombre : desdeDelDia,
      foto: fotos?.lugares[encontrada.parada.recurso.codigo] ?? null,
    };
  }, [abierto, dias, desdeDelDia, fotos]);

  return (
    <>
      {aviso ? <div className="viaje__aviso">{aviso}</div> : null}
      <div className="viaje__cuerpo">
        <header className="portada">
          {portada ? (
            <div className="portada__arte portada__arte--foto">
              <Foto
                foto={portada.foto}
                alt={portada.de}
                sizes="(min-width: 960px) 520px, calc(100vw - 40px)"
                principal
                credito={null}
                alFallar={() => ponerSinFoto(true)}
                className="portada__foto"
              />
              <span className="sello-flor sello-flor--portada">
                <DibujoFlor base={base} puntos={puntos} ida={traslado.horas} resaltado={dia} />
              </span>
              <p className="portada__credito">
                <span className="portada__lugar">{portada.de}</span>
                <span>
                  <CreditoDeFoto foto={portada.foto} />
                </span>
              </p>
            </div>
          ) : (
            <div className="portada__arte">
              <DibujoFlor base={base} puntos={puntos} ida={traslado.horas} resaltado={dia} dibujar />
            </div>
          )}
          <div className="portada__barra">
            <Enlace href={volver} volver className="boton boton--flotante portada__volver">
              <Icono nombre="atras" tamano={20} />
              <span className="boton__texto">Tus viajes</span>
            </Enlace>
            {acciones}
          </div>
          <div className="portada__texto">
            <h1 tabIndex={-1} className="portada__titulo">
              {titulo}
            </h1>
            {subtitulo ? <p className="portada__sub">{subtitulo}</p> : null}
            <ul className="portada__datos">
              <li>
                <Icono nombre="pin" />
                {lista(polo.regiones)}
              </li>
              <li>
                <Icono nombre={excursion ? "reloj" : "cama"} />
                {excursion
                  ? `Ida y vuelta en el día desde ${traslado.desde}`
                  : `Duermes en ${polo.base.nombre}${polo.base.altitud_m != null ? `, a ${metros(polo.base.altitud_m)}` : ""}`}
              </li>
            </ul>
            <DatosClave datos={datosClave(ruta, excursion)} />
          </div>
        </header>

        <Razones ruta={ruta} />
        <AntesDeIr avisos={avisosDelViaje} />

        <div className="recorrido">
          <h2 ref={tituloDelPlan} className="viaje__titular recorrido__titulo">
            Día por día
          </h2>
          <div className="recorrido__selector">
            <SelectorDeDias dias={dias.map((d) => d.dia.numero)} dia={dia} elegirDia={elegirDia} />
          </div>
          <div className="recorrido__mapa">
            <Mapa
              base={base}
              puntos={puntos}
              dia={dia}
              elegirDia={elegirDia}
              abrirLugar={(d, codigo) => ponerAbierto({ dia: d, codigo })}
            />
          </div>
          <div className="recorrido__plan">
            <Itinerario
              dias={dias}
              eventos={eventos}
              dia={dia}
              elegirDia={elegirDia}
              abrirLugar={(d, codigo) => ponerAbierto({ dia: d, codigo })}
            />
            <PlanParaImprimir dias={dias} />
            <Enlace href={enlaces.polo(polo.id, consulta, version)} className="recorrido__zona">
              Ver todos los lugares de la zona
              <Icono nombre="flecha" tamano={16} />
            </Enlace>
          </div>
        </div>

        <section className="viaje__bloque" aria-labelledby="titulo-costo">
          <h2 id="titulo-costo" className="viaje__titular">
            Cuánto cuesta
          </h2>
          <BandaCosto costo={costo} presupuesto={consulta.presupuesto} />
        </section>

        <section className="viaje__bloque" aria-labelledby="titulo-clima">
          <h2 id="titulo-clima" className="viaje__titular">
            El clima en {mes(estacionalidad.mes)}
          </h2>
          <Temporada estacionalidad={estacionalidad} />
        </section>

        {eventos.length > 0 ? (
          <section className="viaje__bloque" aria-labelledby="titulo-fiestas">
            <h2 id="titulo-fiestas" className="viaje__titular">
              Fiestas en tus fechas
            </h2>
            <ListaEventos eventos={eventos} />
            <Enlace
              href={enlaces.calendario(consulta, version, estacionalidad.mes)}
              className="recorrido__zona"
            >
              Ver todas las fiestas de {mes(estacionalidad.mes)}
              <Icono nombre="flecha" tamano={16} />
            </Enlace>
          </section>
        ) : null}

        <footer className="letra-chica">
          <h2 className="letra-chica__titulo">Sobre estos datos</h2>
          <p>
            Las horas son estimadas: el camino, por la red de vías de OpenStreetMap; la visita, según la ficha
            de cada lugar.{" "}
            {excursion
              ? "En el mapa, cada día es un pétalo que abarca sus lugares: muestra qué se ve ese día, no el camino."
              : "En el mapa, cada día es un pétalo que sale de donde duermes y abarca sus lugares: muestra qué se ve ese día, no el camino."}
          </p>
          {avisosDeLosDatos.map((a) => (
            <p key={a.mensaje}>{a.mensaje}</p>
          ))}
          <p>DreemGO no vende ni reserva: los precios son una estimación para que planifiques.</p>
          {fotos ? (
            <p>Las fotos son de Wikimedia Commons: cada una lleva el nombre de su autor y su licencia.</p>
          ) : null}
          <ul className="letra-chica__fuentes">
            {atribucion.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
          <p>{versiones}.</p>
        </footer>
      </div>

      <HojaDeLugar lugar={lugar} alCerrar={() => ponerAbierto(null)} />
    </>
  );
}
