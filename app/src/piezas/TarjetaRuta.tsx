// Una de las tres rutas, resumida para comparar: costo, paradas, días, altitud y km.

import type { Ruta } from "../api/tipos";
import { fijo, km, letra, metros, plural, soles } from "../formato";
import { Enlace } from "./Enlace";
import { Medios, Veredicto } from "./Insignias";

interface Props {
  ruta: Ruta;
  indice: number;
  elegida: boolean;
  enlace: string;
  dias: number;
  alElegir?: () => void;
}

export function TarjetaRuta({ ruta, indice, elegida, enlace, dias, alElegir }: Props) {
  const { polo, costo, indicadores, estacionalidad, traslado } = ruta;
  return (
    <Enlace
      href={enlace}
      reemplazar
      conservarPosicion
      onClick={alElegir}
      className={`tarjeta${elegida ? " tarjeta--elegida" : ""}`}
      aria-current={elegida ? "true" : undefined}
    >
      <span className="tarjeta__cabeza">
        <span className="tarjeta__nombre">
          <span className="tarjeta__letra">Ruta {letra(indice)}</span>
          {polo.nombre}
        </span>
        <span className="tarjeta__costo">
          {soles(costo.p50)}
          <span className="tarjeta__banda">
            entre {soles(costo.p20)} y {soles(costo.p80)}
          </span>
        </span>
      </span>
      <span className="tarjeta__cifras">
        <span>{plural(indicadores.paradas, "parada", "paradas")}</span>
        <span>{plural(dias, "día", "días")}</span>
        {indicadores.altitud_max_m != null ? <span>máx {metros(indicadores.altitud_max_m)}</span> : null}
        <span>{km(indicadores.km_total)}</span>
      </span>
      <span className="tarjeta__insignias">
        <Veredicto veredicto={estacionalidad.veredicto} />
        <Medios medios={traslado.medios ?? ["carretera"]} />
        {polo.fuera_del_circuito ? (
          <span className="insignia insignia--fuerte">Fuera del circuito</span>
        ) : null}
        {indicadores.jerarquia_media != null ? (
          <span className="insignia">Jerarquía media {fijo(indicadores.jerarquia_media)}</span>
        ) : null}
        {costo.dentro_del_presupuesto === false ? (
          <span className="insignia">Pasa tu presupuesto</span>
        ) : null}
      </span>
    </Enlace>
  );
}
