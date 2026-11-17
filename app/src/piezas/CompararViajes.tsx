// Compara las rutas que devolvió esta búsqueda, sin recalcular el orden del motor.
import type { Ruta } from "../api/tipos";
import { fijo, horas, soles } from "../formato";

interface Props {
  rutas: Ruta[];
}

export function CompararViajes({ rutas }: Props) {
  const opciones = rutas.slice(0, 3);
  if (opciones.length < 2) return null;

  // Una misma escala para todas las barras; las cifras escritas son las que importan.
  const maxCosto = Math.max(1, ...opciones.map((ruta) => Math.max(ruta.costo.p50, ruta.costo.p80)));
  const maxTraslado = Math.max(1, ...opciones.map((ruta) => ruta.traslado.horas ?? 0));

  return (
    <section className="comparar-viajes" aria-labelledby="comparar-viajes-titulo">
      <div className="comparar-viajes__entrada">
        <div>
          <p className="comparar-viajes__eyebrow">Tus opciones, lado a lado</p>
          <h2 id="comparar-viajes-titulo">Compara antes de elegir</h2>
        </div>
        <p>
          Costos estimados por persona y horas de ida desde tu origen. Abre una tarjeta para ver el plan
          completo.
        </p>
      </div>

      <ol className="comparar-viajes__lista" aria-label="Comparación de viajes propuestos">
        {opciones.map((ruta, indice) => {
          const p50 = Math.max(0, ruta.costo.p50);
          const p80 = Math.max(p50, ruta.costo.p80);
          const traslado = ruta.traslado.horas;
          return (
            <li className="comparar-viajes__opcion" key={ruta.polo.id}>
              <div className="comparar-viajes__cabecera">
                <span className="comparar-viajes__puesto">Opción {indice + 1}</span>
                <h3>{ruta.polo.nombre}</h3>
              </div>
              <dl className="comparar-viajes__datos">
                <div className="comparar-viajes__dato comparar-viajes__dato--puntaje">
                  <dt>Puntaje de ordenación</dt>
                  <dd>{fijo(ruta.puntaje, 2)}</dd>
                </div>
                <div className="comparar-viajes__dato">
                  <dt>Gasto estimado por persona</dt>
                  <dd>
                    <div className="comparar-viajes__barra comparar-viajes__barra--costo" aria-hidden="true">
                      <span
                        className="comparar-viajes__central"
                        style={{ width: `${(p50 / maxCosto) * 100}%` }}
                      />
                      <span
                        className="comparar-viajes__alto"
                        style={{
                          left: `${(p50 / maxCosto) * 100}%`,
                          width: `${((p80 - p50) / maxCosto) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="comparar-viajes__cifras">
                      <span>
                        P50: <strong>{soles(ruta.costo.p50)}</strong>
                      </span>
                      <span>
                        P80: <strong>{soles(ruta.costo.p80)}</strong>
                      </span>
                    </span>
                  </dd>
                </div>
                <div className="comparar-viajes__dato">
                  <dt>Traslado de ida</dt>
                  <dd>
                    {traslado == null ? (
                      <span>No informado</span>
                    ) : (
                      <>
                        <div
                          className="comparar-viajes__barra comparar-viajes__barra--traslado"
                          aria-hidden="true"
                        >
                          <span style={{ width: `${(Math.max(0, traslado) / maxTraslado) * 100}%` }} />
                        </div>
                        <span>
                          <strong>{horas(traslado)}</strong> desde {ruta.traslado.desde}
                        </span>
                      </>
                    )}
                  </dd>
                </div>
              </dl>
              {ruta.motivos[0] ? (
                <p className="comparar-viajes__motivo">
                  <strong>Por qué aparece:</strong> {ruta.motivos[0]}
                </p>
              ) : null}
            </li>
          );
        })}
      </ol>

      <p className="comparar-viajes__nota">
        El puntaje interno solo ordena las opciones de esta búsqueda: no es una probabilidad. P50 es el costo
        central estimado y P80 un escenario de costo más alto, no precios garantizados.
      </p>
    </section>
  );
}
