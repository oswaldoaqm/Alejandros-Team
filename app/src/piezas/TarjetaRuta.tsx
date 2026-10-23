// Uno de los tres viajes, para elegir de un vistazo: su foto (o su flor, si no tiene), su
// nombre, sus imperdibles y los datos que deciden: cuánto cuesta, cuánto se tarda en llegar (y
// si se vuela o se va en bus de noche), cómo está el clima ese mes y, si se siente, la altura.

import { useMemo, useState } from "react";
import type { Ruta } from "../api/tipos";
import { horas, metros, soles } from "../formato";
import type { FotoDe } from "../fotos";
import { numerar, puntosDeMapa } from "../itinerario";
import {
  ALTURA_QUE_SE_SIENTE,
  climaCorto,
  comoSeVa,
  imperdibles,
  lugaresDelViaje,
  nombreDelViaje,
} from "../textos";
import { Enlace } from "./Enlace";
import { DibujoFlor } from "./Flor";
import { Foto } from "./Foto";
import { Icono, iconoDeLaIda, type NombreDeIcono } from "./Icono";

interface Props {
  ruta: Ruta;
  enlace: string;
  /** Si la etiqueta «Fuera del circuito» distingue a este viaje de los otros dos. */
  marcarFueraDelCircuito: boolean;
  /** La foto del viaje (src/fotos.ts); sin ella, va su flor. */
  foto?: FotoDe | null;
}

const ICONO_DEL_CLIMA: Record<Ruta["estacionalidad"]["veredicto"], NombreDeIcono> = {
  viable: "sol",
  advertencia: "lluvia",
  desaconsejado: "lluvia",
};

export function TarjetaRuta({ ruta, enlace, marcarFueraDelCircuito, foto = null }: Props) {
  const [sinFoto, ponerSinFoto] = useState(false);
  const { polo, costo, indicadores, estacionalidad, traslado } = ruta;
  const { titulo, subtitulo } = nombreDelViaje(polo.nombre);
  const puntos = useMemo(() => puntosDeMapa(numerar(ruta.dias)), [ruta.dias]);
  const base = useMemo(() => ({ lat: polo.base.lat, lon: polo.base.lon }), [polo.base.lat, polo.base.lon]);
  const estrellas = imperdibles(ruta.dias);
  const total = lugaresDelViaje(ruta.dias);
  // El imperdible de más jerarquía da nombre al viaje; el resto se cuenta.
  const principal = estrellas[0];
  const gancho = principal
    ? total > 1
      ? `${principal} y ${total - 1} ${total - 1 === 1 ? "lugar" : "lugares"} más`
      : principal
    : `${total} ${total === 1 ? "lugar" : "lugares"} para visitar`;
  const como = comoSeVa(traslado);
  const maxJerarquia = useMemo(() => {
    return Math.max(0, ...ruta.dias.flatMap((d) => (d.paradas ?? []).map((p) => p.recurso.jerarquia ?? 0)));
  }, [ruta.dias]);

  return (
    <Enlace href={enlace} className="viaje-tarjeta">
      <div className={`viaje-tarjeta__arte${foto && !sinFoto ? " viaje-tarjeta__arte--foto" : ""}`}>
        {foto && !sinFoto ? (
          <>
            <Foto
              foto={foto.foto}
              alt=""
              sizes="(min-width: 720px) 380px, calc(100vw - 40px)"
              tope={960}
              credito="texto"
              alFallar={() => ponerSinFoto(true)}
              className="viaje-tarjeta__foto"
            />
            <span className="sello-flor">
              <DibujoFlor base={base} puntos={puntos} ida={traslado.horas} />
            </span>
          </>
        ) : (
          <DibujoFlor base={base} puntos={puntos} ida={traslado.horas} />
        )}
        <div className="viaje-tarjeta__sellos">
          {marcarFueraDelCircuito && polo.fuera_del_circuito ? (
            <span className="viaje-tarjeta__sello">Fuera del circuito</span>
          ) : null}
          {maxJerarquia >= 3 ? (
            <span
              className={`viaje-tarjeta__sello viaje-tarjeta__sello--j${maxJerarquia}`}
              title={
                maxJerarquia === 4
                  ? "Atractivo de jerarquía 4 (Significación internacional según MINCETUR)"
                  : "Atractivo de jerarquía 3 (Significación nacional según MINCETUR)"
              }
            >
              <Icono nombre="escudo" tamano={12} />
              Jerarquía {maxJerarquia} · MINCETUR
            </span>
          ) : null}
        </div>
      </div>
      <div className="viaje-tarjeta__cuerpo">
        <h2 className="viaje-tarjeta__nombre">
          {titulo}
          {subtitulo ? <span className="viaje-tarjeta__sub">{subtitulo}</span> : null}
        </h2>
        <p className="viaje-tarjeta__gancho">
          {principal ? <Icono nombre="estrella" relleno tamano={15} /> : null}
          {gancho}
        </p>
        <ul className="viaje-tarjeta__datos">
          <li className="viaje-tarjeta__precio">
            <span className="num">{soles(costo.p50)}</span> por persona{" "}
            {costo.dentro_del_presupuesto === false && costo.exceso != null ? (
              <span className="viaje-tarjeta__exceso">{soles(costo.exceso)} sobre tu presupuesto</span>
            ) : null}
          </li>
          {traslado.horas != null ? (
            <li>
              <Icono nombre={iconoDeLaIda(traslado.medios)} />
              {horas(traslado.horas)} desde {traslado.desde}
              {como ? `, ${como}` : null}
            </li>
          ) : null}
          <li>
            <Icono nombre={ICONO_DEL_CLIMA[estacionalidad.veredicto]} />
            {climaCorto(estacionalidad.veredicto, estacionalidad.mes)}
          </li>
          {indicadores.altitud_max_m != null && indicadores.altitud_max_m >= ALTURA_QUE_SE_SIENTE ? (
            <li>
              <Icono nombre="montana" />
              Hasta {metros(indicadores.altitud_max_m)} de altura
            </li>
          ) : null}
        </ul>
      </div>
    </Enlace>
  );
}
