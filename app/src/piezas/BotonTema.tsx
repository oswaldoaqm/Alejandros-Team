// Interruptor de modo claro / modo oscuro, inspirado en «¿Y tú qué planes?».
// Arranca con el tema del sistema; lo que la persona elige aquí queda guardado (src/estado/tema.ts).

import { useTema } from "../estado/tema";

export function BotonTema() {
  const [tema, alternar] = useTema();
  const esOscuro = tema === "dark";

  return (
    <button
      type="button"
      className="conmutador-tema"
      onClick={alternar}
      role="switch"
      aria-checked={esOscuro}
      aria-label={`Cambiar a ${esOscuro ? "modo claro" : "modo oscuro"}`}
      title={`Cambiar a ${esOscuro ? "modo claro" : "modo oscuro"}`}
    >
      <span className="conmutador-tema__etiqueta">{esOscuro ? "Modo oscuro" : "Modo claro"}</span>
      <span className="conmutador-tema__pista" aria-hidden="true">
        {esOscuro ? (
          <span className="conmutador-tema__icono conmutador-tema__icono--luna">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </span>
        ) : null}
        <span className={`conmutador-tema__perilla conmutador-tema__perilla--${tema}`} />
        {!esOscuro ? (
          <span className="conmutador-tema__icono conmutador-tema__icono--sol">
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="4" fill="currentColor" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
            </svg>
          </span>
        ) : null}
      </span>
    </button>
  );
}
