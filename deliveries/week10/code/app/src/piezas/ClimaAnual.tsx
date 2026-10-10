// El clima de una zona en los doce meses: la lluvia de cada mes como barra y su veredicto
// debajo, con ícono. Al elegir un mes se lee su explicación; la tabla dice lo mismo en números.

import { useId, useState } from "react";
import type { Estacionalidad, Veredicto as TipoVeredicto } from "../api/tipos";
import { decimal, MESES_CORTOS, mayuscula, mes } from "../formato";
import { Icono, type NombreDeIcono } from "./Icono";
import { Veredicto } from "./Insignias";

const ICONO: Record<TipoVeredicto, NombreDeIcono> = {
  viable: "bien",
  advertencia: "aviso",
  desaconsejado: "critico",
};
const PALABRA: Record<TipoVeredicto, string> = {
  viable: "buen mes",
  advertencia: "con advertencia",
  desaconsejado: "desaconsejado",
};

function milimetros(n: number): string {
  return `${decimal(n, 0)} mm`;
}

export function ClimaAnual({ clima, inicial }: { clima: Estacionalidad[]; inicial: number }) {
  const id = useId();
  const meses = [...clima].sort((a, b) => a.mes - b.mes);
  const [elegido, elegir] = useState(inicial);
  const actual = meses.find((m) => m.mes === elegido) ?? meses[0];
  if (!actual) return null;
  const tope = Math.max(1, ...meses.map((m) => m.lluvia_mm));

  return (
    <div className="clima">
      <fieldset className="clima__grafico">
        <legend className="solo-lector">
          Lluvia y veredicto de cada mes. Elige un mes para leer su explicación.
        </legend>
        <p className="clima__tope" aria-hidden="true">
          {milimetros(tope)}
        </p>
        <div className="clima__meses">
          {meses.map((m) => (
            <label key={m.mes} className={`clima__mes clima__mes--${m.veredicto}`}>
              <input
                type="radio"
                name={`${id}-mes`}
                className="solo-lector"
                checked={m.mes === actual.mes}
                onChange={() => elegir(m.mes)}
              />
              <span className="solo-lector">
                {mayuscula(mes(m.mes))}: {milimetros(m.lluvia_mm)} de lluvia, {PALABRA[m.veredicto]}
              </span>
              <span className="clima__columna" aria-hidden="true">
                <span
                  className="clima__barra"
                  style={{ height: `${Math.max(2, (m.lluvia_mm / tope) * 100)}%` }}
                />
              </span>
              <span className="clima__estado" aria-hidden="true">
                <Icono nombre={ICONO[m.veredicto]} tamano={15} />
              </span>
              <span className="clima__nombre" aria-hidden="true">
                {mayuscula(MESES_CORTOS[m.mes - 1] ?? "")}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="clima__lectura" aria-live="polite">
        <p>
          <strong>{mayuscula(mes(actual.mes))}</strong> · {milimetros(actual.lluvia_mm)} de lluvia{" "}
          <Veredicto veredicto={actual.veredicto} />
        </p>
        <p>{actual.explicacion}</p>
      </div>

      <p className="ayuda clima__clave">
        Barras: lluvia media del mes.{" "}
        <span className="clima__estado clima__mes--viable">
          <Icono nombre="bien" tamano={14} />
        </span>{" "}
        buen mes ·{" "}
        <span className="clima__estado clima__mes--advertencia">
          <Icono nombre="aviso" tamano={14} />
        </span>{" "}
        con advertencia ·{" "}
        <span className="clima__estado clima__mes--desaconsejado">
          <Icono nombre="critico" tamano={14} />
        </span>{" "}
        desaconsejado
      </p>

      <details className="plegable">
        <summary>Ver como tabla</summary>
        <div className="tabla-marco">
          <table>
            <caption className="solo-lector">Clima de la zona, mes a mes</caption>
            <thead>
              <tr>
                <th scope="col">Mes</th>
                <th scope="col" className="num">
                  Lluvia
                </th>
                <th scope="col" className="num">
                  Días con lluvia
                </th>
                <th scope="col" className="num">
                  Temperatura
                </th>
                <th scope="col">Veredicto</th>
              </tr>
            </thead>
            <tbody>
              {meses.map((m) => (
                <tr key={m.mes}>
                  <th scope="row">{mayuscula(mes(m.mes))}</th>
                  <td className="num">{milimetros(m.lluvia_mm)}</td>
                  <td className="num">{m.dias_con_lluvia != null ? decimal(m.dias_con_lluvia, 0) : "—"}</td>
                  <td className="num">
                    {m.temp_min_c != null && m.temp_max_c != null
                      ? `${decimal(m.temp_min_c, 0)} a ${decimal(m.temp_max_c, 0)} °C`
                      : "—"}
                  </td>
                  <td>{mayuscula(PALABRA[m.veredicto])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
