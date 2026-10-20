// Cómo funciona DreemGO, de dónde salen sus datos y qué no hace. Texto fijo: lo que cambia
// con los datos (versión, fuentes de cada respuesta) se muestra junto a cada resultado.

import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { metros } from "../formato";
import { Enlace, EnlaceExterno } from "../piezas/Enlace";
import { enlaces } from "../ruta";

const REPOSITORIO = "https://github.com/oswaldoaqm/Alejandros-Team";
const CDC_ALTURA =
  "https://www.cdc.gov/yellow-book/hcp/environmental-hazards-risks/high-altitude-travel-and-altitude-illness.html";

export function Acerca() {
  const { opciones } = useApp();
  useTitulo("Cómo funciona");
  return (
    <section className="pagina pagina--angosta prosa">
      <h1 tabIndex={-1} className="pagina__titulo">
        Cómo funciona
      </h1>
      <p className="pagina__bajada">
        DreemGO propone hasta tres viajes dentro del Perú para lo que le pidas, día por día. No vende ni
        reserva: estima, y te deja verificar cada lugar en su fuente oficial.
      </p>

      <h2>De dónde salen los lugares</h2>
      <p>
        Del Inventario Nacional de Recursos Turísticos de MINCETUR. Cada lugar enlaza a su ficha oficial, y su
        importancia es la jerarquía que le asigna el ministerio, de 1 a 4: desde 3, DreemGO lo marca como
        imperdible. Cuando la ficha no trae un dato —la jerarquía, la tarifa—, DreemGO lo dice en vez de
        inventarlo.
      </p>

      <h2>Cómo arma un viaje</h2>
      <ol>
        <li>
          Agrupa los lugares cercanos en zonas: cada una se recorre durmiendo en un mismo pueblo. Si la zona
          queda cerca de donde sales, el viaje puede ser de ida y vuelta en el día.
        </li>
        <li>
          Reparte tus días entre la ida, la vuelta y los días en la zona. Lo que por tierra queda a entre 7 y
          16 horas se hace en bus de noche: sales la noche antes del día 1, vuelves la noche del último y tus
          días son todos allá. En un viaje corto, solo si el bus no se lleva demasiado: en dos días, hasta
          unas 9 horas y media por tramo. A lo que queda a más de 16 horas se va en avión, si el viaje no es
          corto y no pediste ir solo por tierra.
        </li>
        <li>
          Cada día es un paseo que sale de donde duermes y vuelve: hasta 8 horas y seis lugares, más una hora
          para almorzar, así que un día entero va de 8:00 a 17:00. El almuerzo va donde hay dónde comer cerca,
          según OpenStreetMap y Overture Maps; si cerca no tienen nada registrado, el plan te dice que lo
          lleves.
        </li>
        <li>
          En la altura, el primer día va con calma. Si duermes a {metros(2500)} o más y llegas desde{" "}
          {metros(1000)} o más abajo, ese día tiene medio día de visitas como mucho, ningún lugar a más de{" "}
          {metros(500)} sobre donde duermes y ninguna caminata larga; después de un bus de noche, empieza a
          las 9:00. El <EnlaceExterno href={CDC_ALTURA}>Yellow Book del CDC</EnlaceExterno> de Estados Unidos
          aconseja solo ejercicio suave en las primeras {"48\u00a0horas"} en la altura.
        </li>
        <li>
          Elige qué visitar y en qué orden para aprovechar el tiempo: un lugar más importante vale más, y si
          marcaste intereses, los que los atienden pesan más.
        </li>
        <li>
          Ordena las zonas con un puntaje que combina cuánto vale lo que se visita, si el mes conviene, si
          entra en tu presupuesto, si hay dónde salir de noche cuando pediste vida nocturna y cuánto se aleja
          del circuito de Lima y Cusco. Las dos noches en un bus pesan como un día más de viaje, para que un
          fin de semana no salga siempre lejos. Un viaje que pasa tu presupuesto sale solo si es mucho mejor
          que los que entran, y siempre con su aviso. «Sorpréndeme» busca solo fuera de ese circuito.
        </li>
      </ol>
      <p>
        Si eliges a dónde ir, arma solo el viaje a esa zona, con las mismas reglas: es el mismo viaje que te
        propondría si la eligiera él, salvo por el avión, que con la zona elegida se toma aunque el viaje sea
        corto. Si no cabe, te dice por qué y qué cambiar para que salga: cuántos días hacen falta, si volando
        sí, o ver viajes a otras zonas.
      </p>

      <h2>De noche</h2>
      <p>
        Las noches que duermes en la zona, el plan propone qué hacer. Con «Vida nocturna», dónde salir: bares,
        pubs, discotecas, karaokes y peñas a no más de unos 25 minutos a pie de donde duermes, otros cada
        noche. Salen de OpenStreetMap y de Overture Maps, que junta lo que publican Meta y Microsoft; un bar
        puede haber cerrado, así que cada uno enlaza a su mapa para verificarlo. La primera noche en la
        altura, si llegas de abajo, el plan propone descansar.
      </p>
      <p>
        Con «Naturaleza», o sin ningún interés, una noche para ver estrellas donde el cielo es oscuro. Cuánta
        luz artificial hay en el cielo se estima con las luces que ve de noche el satélite VIIRS y un modelo
        publicado (Duriscoe y otros, 2018), con las clases del Servicio de Parques Nacionales de Estados
        Unidos. Cuántas noches salen despejadas cada mes, con la máscara de nubes del satélite GOES-16 de 2022
        a 2024; en la costa, donde de noche el satélite no ve las nubes bajas, con lo que reportó el
        aeropuerto más cercano. Con fecha, la noche elegida es la de menos luna, y el plan dice a qué hora
        oscurece y cuándo sale o se pone.
      </p>

      <h2>El mes</h2>
      <p>
        El veredicto de cada mes —buen mes, con advertencia o desaconsejado— sale de diez años de lluvia en la
        zona. Es una regla escrita sobre el clima pasado, no un pronóstico: sirve para elegir el mes, no para
        saber si lloverá un día en particular.
      </p>

      <h2>El costo</h2>
      <p>
        Es una banda y no un precio: lo más probable es que el gasto por persona caiga entre sus dos extremos.
        Suma transporte, los vuelos si los hay, hospedaje económico, alimentación y las entradas que publican
        las fichas. Las noches en un bus de noche no se pagan como hospedaje, y el bus se cobra a la misma
        tarifa por kilómetro que de día. Los supuestos van al lado de cada costo.
      </p>

      <h2>Las fiestas y los eventos</h2>
      <p>
        El calendario sale de dos lugares. Las fiestas y ferias del inventario de MINCETUR, con su fecha
        calculada cuando la ficha no la trae; y los eventos que publican las municipalidades y las oficinas de
        destino, con sus fechas exactas y el nombre de quien los publicó. Un evento publicado se suma a los
        viajes que pasan cerca, pero no cambia qué viajes se proponen ni en qué orden: el orden no se vende.{" "}
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
        <li>Un viaje visita una sola zona. Combinar varias en un mismo viaje es lo siguiente.</li>
        <li>
          No conoce horarios ni disponibilidad de buses, trenes, botes u hospedajes: el bus de noche sale a la
          hora que deja llegar a eso de las 6:00.
        </li>
        <li>
          Una visita larga que empieza antes del almuerzo, como una caminata de varias horas, lo corre hasta
          que termina.
        </li>
        <li>No sabe si un bar o una discoteca sigue abierto ni qué noches abre.</li>
        <li>
          Solo el primer día en la altura va con calma, aunque el CDC habla de las primeras {"48\u00a0horas"}.
        </li>
      </ul>

      <h2>Tus datos</h2>
      <p>
        No hay cuentas ni contraseñas. La consulta viaja en el enlace: compartir el enlace es compartir el
        viaje. Lo que guardas en «Guardados» queda solo en tu navegador.
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
          Lugares para salir y para comer:{" "}
          <EnlaceExterno href="https://overturemaps.org/">Overture Maps Foundation</EnlaceExterno>, con datos
          de Meta y Microsoft, CDLA Permissive 2.0; y OpenStreetMap.
        </li>
        <li>
          Luces nocturnas: VIIRS, del{" "}
          <EnlaceExterno href="https://eogdata.mines.edu/products/vnl/">
            Earth Observation Group de la Colorado School of Mines
          </EnlaceExterno>
          , de dominio público, en la copia{" "}
          <EnlaceExterno href="https://registry.opendata.aws/wb-light-every-night/">
            «Light Every Night» del Banco Mundial
          </EnlaceExterno>
          . Nubes: GOES-16 y los METAR de los aeropuertos, de{" "}
          <EnlaceExterno href="https://www.noaa.gov/">NOAA</EnlaceExterno>.
        </li>
        <li>
          Altura del terreno, donde OpenStreetMap no la trae:{" "}
          <EnlaceExterno href="https://registry.opendata.aws/terrain-tiles/">Terrain Tiles</EnlaceExterno>, en
          el registro de datos abiertos de AWS, con SRTM y GMTED2010 del U.S. Geological Survey, de dominio
          público.
        </li>
        <li>
          Mapa de fondo: <EnlaceExterno href="https://openfreemap.org/">OpenFreeMap</EnlaceExterno>, con
          OpenMapTiles y datos de OpenStreetMap.
        </li>
        <li>
          Fotos: <EnlaceExterno href="https://commons.wikimedia.org/">Wikimedia Commons</EnlaceExterno>,
          elegidas con Wikidata. Cada una lleva el nombre de su autor y su licencia, y enlaza a su página.
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
