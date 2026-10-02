// Cómo funciona DreemGO, de dónde salen sus datos y qué no hace. Texto fijo: lo que cambia
// con los datos (versión, fuentes de cada respuesta) se muestra junto a cada resultado.

import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { Enlace, EnlaceExterno } from "../piezas/Enlace";
import { enlaces } from "../ruta";

const REPOSITORIO = "https://github.com/oswaldoaqm/Alejandros-Team";

export function Acerca() {
  const { opciones } = useApp();
  useTitulo("Cómo funciona");
  return (
    <section className="pagina pagina--angosta prosa">
      <h1 tabIndex={-1}>Cómo funciona</h1>
      <p className="bajada">
        DreemGO propone hasta tres viajes dentro del Perú para lo que le pidas, día por día. No vende ni
        reserva: estima, y te deja verificar cada lugar en su fuente oficial.
      </p>

      <h2>De dónde salen los lugares</h2>
      <p>
        Del Inventario Nacional de Recursos Turísticos de MINCETUR. Cada parada enlaza a su ficha oficial, y
        la jerarquía (de 1 a 4) es la que el ministerio le asigna. Cuando la ficha no trae un dato —la
        jerarquía, la tarifa—, DreemGO lo dice en vez de inventarlo.
      </p>

      <h2>Cómo arma un viaje</h2>
      <ol>
        <li>
          Agrupa los lugares cercanos en <strong>polos</strong>: zonas que se recorren durmiendo en un mismo
          pueblo, la base.
        </li>
        <li>
          Reparte tus días entre la ida, la vuelta y los días en la base. Cada día sale un paseo que vuelve a
          la base, con jornadas de hasta 8 horas y hasta seis paradas.
        </li>
        <li>
          Elige qué visitar y en qué orden para aprovechar el tiempo: un lugar de mayor jerarquía vale más, y
          si marcaste intereses, los que los atienden pesan más.
        </li>
        <li>
          Ordena los polos con un puntaje que combina cuánto vale lo que se visita, si el mes conviene, si
          entra en tu presupuesto y cuánto se aleja del circuito de Lima y Cusco. El presupuesto ordena y
          avisa, pero no esconde ninguna ruta. «Sorpréndeme» busca solo fuera de ese circuito.
        </li>
      </ol>

      <h2>El mes</h2>
      <p>
        El veredicto de cada mes —buen mes, con advertencia o desaconsejado— sale de diez años de lluvia en la
        zona del polo. Es una regla escrita sobre el clima pasado, no un pronóstico: sirve para elegir el mes,
        no para saber si lloverá un día en particular.
      </p>

      <h2>El costo</h2>
      <p>
        Es una banda y no un precio: lo más probable es que el gasto por persona caiga entre sus dos extremos.
        Suma transporte, hospedaje económico, alimentación y las entradas que publican las fichas. Los
        supuestos van al lado de cada costo.
      </p>

      <h2>Las fiestas y los eventos</h2>
      <p>
        El calendario sale de dos lugares. Las fiestas y ferias del inventario de MINCETUR, con su fecha
        calculada cuando la ficha no la trae; y los eventos que publican las municipalidades y las oficinas de
        destino, con sus fechas exactas y el nombre de quien los publicó. Un evento publicado se suma a las
        rutas que pasan cerca, pero no cambia qué rutas se proponen ni en qué orden: el orden no se vende.{" "}
        <Enlace href={enlaces.publicar()}>Publicar un evento</Enlace>
      </p>

      <h2>Los tiempos de viaje</h2>
      <p>
        Se calculan sobre las vías, el tren y las rutas de bote de OpenStreetMap, con velocidades ajustadas
        con los recorridos que describen las fichas oficiales. Son estimaciones: no cuentan el tráfico del
        día, los horarios de los buses ni las esperas.
      </p>

      <h2>Lo que todavía no hace</h2>
      <ul>
        <li>Un viaje visita un solo polo. Combinar varios en un mismo viaje es lo siguiente.</li>
        <li>No conoce horarios ni disponibilidad de buses, trenes, botes u hospedajes.</li>
        <li>
          Donde todavía no se cargó el clima propio de un polo, usa el promedio de su región y lo avisa en la
          ruta.
        </li>
      </ul>

      <h2>Tus datos</h2>
      <p>
        No hay cuentas ni contraseñas. La consulta viaja en el enlace: compartir el enlace es compartir el
        viaje. «Mis viajes» se guarda solo en tu navegador.
      </p>

      <h2>Fuentes y licencias</h2>
      <ul>
        <li>
          Lugares, fichas y calendario de fiestas:{" "}
          <EnlaceExterno href="https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos">
            Inventario Nacional de Recursos Turísticos
          </EnlaceExterno>
          , MINCETUR, ODC-BY 1.0.
        </li>
        <li>
          Clima: <EnlaceExterno href="https://open-meteo.com/">Open-Meteo</EnlaceExterno>, sobre ERA5 y
          ERA5-Land de Copernicus, CC BY 4.0.
        </li>
        <li>
          Vías, trenes, botes, pueblos y hospedajes: ©{" "}
          <EnlaceExterno href="https://www.openstreetmap.org/copyright">
            colaboradores de OpenStreetMap
          </EnlaceExterno>
          , ODbL 1.0.
        </li>
        <li>
          Mapa de fondo: <EnlaceExterno href="https://openfreemap.org/">OpenFreeMap</EnlaceExterno>, con
          OpenMapTiles y datos de OpenStreetMap.
        </li>
      </ul>

      <h2>Quién lo hace</h2>
      <p>
        Alejandro's Team, para el curso DS3022 Desarrollo de Producto de Datos de UTEC, ciclo 2026-2. El
        código, los datos procesados y el porqué de cada decisión están en{" "}
        <EnlaceExterno href={REPOSITORIO}>el repositorio del proyecto</EnlaceExterno>, con licencia MIT.
      </p>
      {opciones.datos ? (
        <p className="procedencia">
          Datos {opciones.datos.version_datos} · contrato {opciones.datos.version_contrato}
        </p>
      ) : null}

      <p>
        <Enlace href={enlaces.inicio()} className="boton boton--primario">
          Armar un viaje
        </Enlace>
      </p>
    </section>
  );
}
