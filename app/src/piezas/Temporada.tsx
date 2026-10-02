// Si el mes conviene: el veredicto con su explicación, el clima del mes y los mejores meses.

import type { Estacionalidad } from "../api/tipos";
import { decimal, lista, MESES_CORTOS, mayuscula, mes, rangosDeMeses } from "../formato";
import { Veredicto } from "./Insignias";

export function Temporada({ estacionalidad: e }: { estacionalidad: Estacionalidad }) {
  const mejores = e.mejores_meses ?? [];
  const cifras: [string, string][] = [["Lluvia del mes", `${decimal(e.lluvia_mm, 0)} mm`]];
  if (e.dias_con_lluvia != null) cifras.push(["Días con lluvia", decimal(e.dias_con_lluvia, 0)]);
  if (e.temp_min_c != null && e.temp_max_c != null) {
    cifras.push(["Temperatura", `${decimal(e.temp_min_c, 0)} a ${decimal(e.temp_max_c, 0)} °C`]);
  }
  if (e.horas_sol != null) cifras.push(["Sol al día", `${decimal(e.horas_sol)} h`]);

  return (
    <div className="temporada">
      <p>
        <Veredicto veredicto={e.veredicto} />
      </p>
      <p>{e.explicacion}</p>
      <dl className="cifras">
        {cifras.map(([nombre, valor]) => (
          <div key={nombre}>
            <dt>{nombre}</dt>
            <dd>{valor}</dd>
          </div>
        ))}
      </dl>
      {mejores.length > 0 ? (
        <>
          <ol className="tira-meses" aria-hidden="true">
            {MESES_CORTOS.map((corto, indice) => {
              const numero = indice + 1;
              const clases = ["tira-meses__mes"];
              if (mejores.includes(numero)) clases.push("tira-meses__mes--mejor");
              if (numero === e.mes) clases.push("tira-meses__mes--elegido");
              return (
                <li key={corto} className={clases.join(" ")}>
                  {mayuscula(corto.charAt(0))}
                </li>
              );
            })}
          </ol>
          <p className="ayuda">
            <span className="tira-meses__clave tira-meses__clave--mejor" aria-hidden="true" /> Mejores meses:{" "}
            {rangosDeMeses(mejores)}.
            {mejores.length > 3
              ? ` Los de menos lluvia: ${lista(mejores.slice(0, 3).map((m) => mes(m)))}.`
              : ""}{" "}
            <span className="tira-meses__clave tira-meses__clave--elegido" aria-hidden="true" /> Tu mes:{" "}
            {mes(e.mes)}.
          </p>
        </>
      ) : null}
    </div>
  );
}
