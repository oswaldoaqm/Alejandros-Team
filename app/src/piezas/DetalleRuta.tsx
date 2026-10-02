// Todo lo de una ruta: por qué se propone, sus avisos, el mapa, el itinerario, el costo, el
// mes y los eventos. Devuelve tres bloques que la pantalla de resultados acomoda: en celular
// van uno debajo del otro; en pantalla ancha, el mapa queda fijo a la izquierda.

import { useMemo, useRef, useState } from "react";
import type { Ruta } from "../api/tipos";
import type { Consulta } from "../consulta";
import { fijo, horas, km, letra, lista, mayuscula, mes, metros, plural } from "../formato";
import { esExcursion, numerar, puntosDeMapa } from "../itinerario";
import { llevarA } from "../movimiento";
import { enlaces } from "../ruta";
import { conQueSeViaja } from "../textos";
import { BandaCosto } from "./BandaCosto";
import { Enlace } from "./Enlace";
import { Icono } from "./Icono";
import { Itinerario } from "./Itinerario";
import { ListaAvisos, ListaEventos } from "./Listas";
import { Mapa } from "./Mapa";
import { Temporada } from "./Temporada";

interface Props {
  ruta: Ruta;
  indice: number;
  consulta: Consulta;
  version: string | null;
}

export function DetalleRuta({ ruta, indice, consulta, version }: Props) {
  const { polo, traslado, costo, indicadores, estacionalidad } = ruta;
  const [dia, elegirDia] = useState<number | null>(null);
  const marco = useRef<HTMLDivElement>(null);

  const dias = useMemo(() => numerar(ruta.dias), [ruta.dias]);
  const puntos = useMemo(() => puntosDeMapa(dias), [dias]);
  const excursion = esExcursion(ruta);
  const { nombre, lat, lon } = polo.base;
  const base = useMemo(() => (excursion ? null : { nombre, lat, lon }), [excursion, nombre, lat, lon]);
  const diasConParadas = dias.filter((d) => d.paradas.length > 0).map((d) => d.dia.numero);
  const eventos = ruta.eventos ?? [];

  const verEnMapa = (numero: number) => {
    elegirDia(numero);
    llevarA(marco.current, "nearest");
  };

  const cifras: [string, string][] = [
    ["Paradas", String(indicadores.paradas)],
    ["De jerarquía 3 o 4", String(indicadores.paradas_jerarquia_alta)],
  ];
  if (indicadores.jerarquia_media != null)
    cifras.push(["Jerarquía media", fijo(indicadores.jerarquia_media)]);
  if (indicadores.altitud_max_m != null) cifras.push(["Parada más alta", metros(indicadores.altitud_max_m)]);
  cifras.push(["Recorrido total", km(indicadores.km_total)]);
  cifras.push(["Del valor del polo", `${Math.round(indicadores.valor_capturado * 100)}\u00a0%`]);

  return (
    <>
      <div className="detalle__cabeza">
        <h2 id="detalle" tabIndex={-1}>
          <span className="rotulo">Ruta {letra(indice)}</span>
          {polo.nombre}
        </h2>
        <p className="detalle__resumen">
          {lista(polo.regiones)} ·{" "}
          {excursion ? (
            <>
              ida y vuelta en el día
              {traslado.horas != null
                ? `; la primera parada queda a ${horas(traslado.horas)} de ${traslado.desde}`
                : ""}
            </>
          ) : (
            <>
              se duerme en {polo.base.nombre}
              {polo.base.altitud_m != null ? ` (${metros(polo.base.altitud_m)})` : ""}
              {traslado.horas != null
                ? ` · ${horas(traslado.horas)} de ida desde ${traslado.desde}, ${conQueSeViaja(traslado.medios)}`
                : ""}
            </>
          )}
          .{" "}
          <Enlace href={enlaces.polo(polo.id, consulta, version)}>
            Ver todo lo que hay en el polo
            <Icono nombre="flecha" tamano={14} />
          </Enlace>
        </p>

        {ruta.motivos.length > 0 ? (
          <>
            <h3 className="rotulo">Por qué esta ruta</h3>
            <ul className="motivos">
              {ruta.motivos.map((m) => (
                <li key={m}>
                  <Icono nombre="bien" tamano={16} />
                  <span>{m}</span>
                </li>
              ))}
            </ul>
          </>
        ) : null}

        <ListaAvisos avisos={ruta.avisos ?? []} />
      </div>

      <div className="detalle__mapa" ref={marco}>
        <h3 className="rotulo">
          El recorrido en el mapa · {plural(indicadores.paradas, "parada", "paradas")}
        </h3>
        <Mapa base={base} puntos={puntos} dia={dia} dias={diasConParadas} elegirDia={elegirDia} />
      </div>

      <div className="detalle__resto">
        <section aria-labelledby="titulo-itinerario">
          <h3 className="rotulo" id="titulo-itinerario">
            Itinerario día por día
          </h3>
          <Itinerario
            dias={dias}
            eventos={eventos}
            desde={excursion ? traslado.desde : polo.base.nombre}
            verEnMapa={verEnMapa}
          />
          <p className="ayuda">
            Las horas son estimadas: el viaje por la red de vías de OpenStreetMap y la visita según la ficha
            de cada lugar. J es la jerarquía que MINCETUR le da al lugar, de 1 a 4.
          </p>
        </section>

        <section aria-labelledby="titulo-costo">
          <h3 className="rotulo" id="titulo-costo">
            Cuánto cuesta
          </h3>
          <BandaCosto costo={costo} presupuesto={consulta.presupuesto} />
        </section>

        <section aria-labelledby="titulo-mes">
          <h3 className="rotulo" id="titulo-mes">
            {mayuscula(mes(estacionalidad.mes))} en {polo.nombre}
          </h3>
          <Temporada estacionalidad={estacionalidad} />
        </section>

        <section aria-labelledby="titulo-eventos">
          <h3 className="rotulo" id="titulo-eventos">
            Fiestas y eventos en tus fechas
          </h3>
          <ListaEventos
            eventos={eventos}
            vacio="El calendario oficial no registra fiestas ni eventos de este polo en esas fechas."
          />
        </section>

        <section aria-labelledby="titulo-cifras">
          <h3 className="rotulo" id="titulo-cifras">
            La ruta en números
          </h3>
          <dl className="cifras">
            {cifras.map(([nombreDeCifra, valor]) => (
              <div key={nombreDeCifra}>
                <dt>{nombreDeCifra}</dt>
                <dd>{valor}</dd>
              </div>
            ))}
          </dl>
          <p className="ayuda">
            «Del valor del polo» es cuánto de lo que se puede visitar con tu consulta entra en el itinerario,
            contando más los lugares de mayor jerarquía.
          </p>
        </section>
      </div>
    </>
  );
}
