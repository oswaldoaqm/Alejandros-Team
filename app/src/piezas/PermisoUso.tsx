import { useEffect, useState } from "react";
import { estadisticasPermitidas, iniciarEstadisticas, permitirEstadisticas } from "../analitica";

/** El visitante decide si sus acciones anónimas ayudan a evaluar la app. */
export function PermisoUso({ registrarInicio = true }: { registrarInicio?: boolean }) {
  const [permitido, ponerPermitido] = useState(estadisticasPermitidas);
  const [aviso, ponerAviso] = useState("");

  useEffect(() => {
    if (registrarInicio) iniciarEstadisticas();
  }, [registrarInicio]);

  return (
    <div className="permiso-uso">
      <label>
        <input
          type="checkbox"
          checked={permitido}
          onChange={(evento) => {
            const nuevo = evento.target.checked;
            if (!permitirEstadisticas(nuevo)) {
              ponerAviso("Este navegador no permite guardar tu elección.");
              return;
            }
            ponerPermitido(nuevo);
            ponerAviso(nuevo ? "Estadísticas anónimas activadas." : "Estadísticas anónimas desactivadas.");
            if (nuevo && registrarInicio) iniciarEstadisticas();
          }}
        />
        <span>Compartir estadísticas anónimas para mejorar DreemGO</span>
      </label>
      <p>Opcional. Registra acciones y filtros del viaje, sin nombre ni correo. Puedes desactivarlo aquí.</p>
      <span role="status" className="solo-lector">
        {aviso}
      </span>
    </div>
  );
}
