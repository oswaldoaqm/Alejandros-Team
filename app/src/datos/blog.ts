// Artículos y notas del Blog viajero, inspirados en el formato editorial de ¿Y tú qué planes?
// Incluyen destinos de Perú, sugerencias prácticas y enlace directo para planear el viaje.

import type { Foto } from "../fotos";

export type CategoriaBlog =
  | "experiencia"
  | "gastronomia"
  | "festividades"
  | "viajes con propósito"
  | "artesanías"
  | "naturaleza"
  | "aventura";

export interface ArticuloBlog {
  id: string;
  slug: string;
  titulo: string;
  extracto: string;
  categoria: CategoriaBlog;
  lugar: string;
  region: string;
  fecha: string;
  tiempoLectura: string;
  destacadoEnHome?: boolean;
  destinoId: number;
  foto: Foto;
  parrafos: string[];
  imperdibles: string[];
  consejos: string[];
}

export const ARTICULOS_BLOG: ArticuloBlog[] = [
  {
    id: "virgen-candelaria-puno",
    slug: "virgen-de-la-candelaria-puno",
    titulo:
      "Virgen de la Candelaria 2027: todo sobre su presentación oficial en Lima y la festividad en Puno",
    extracto:
      "La mayor fiesta del folclore peruano alista sus mejores galas. Conoce las fechas de las comparsas, la Misa de Albas y cómo planificar tu estancia en la Capital del Folklore.",
    categoria: "festividades",
    lugar: "Puno",
    region: "Puno",
    fecha: "03/11/2026",
    tiempoLectura: "5 min de lectura",
    destacadoEnHome: true,
    destinoId: 11,
    foto: {
      archivo: "Vista de Puno y el Titicaca, Perú, 2015-08-01, DD 53-54 PAN.JPG",
      ruta: "4/42",
      ancho: 4096,
      alto: 1536,
      autor: "Diego Delso",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "Q232842",
    },
    parrafos: [
      "Cada febrero, la ciudad de Puno se convierte en el epicentro cultural y espiritual del continente con la celebración de la Virgen de la Candelaria, declarada Patrimonio Cultural Inmaterial de la Humanidad por la UNESCO.",
      "Más de 40.000 danzantes y 200 bandas de música recorren las calles de la ciudad andina interpretando morenadas, diabladas, caporales, waca wacas y sikuris con trajes bordados a mano repletos de pedrería y plata.",
      "Para quienes viajan por primera vez, es fundamental reservar pasajes y hospedaje con al menos tres meses de anticipación, ya que la capacidad hotelera de Puno y Juliaca suele alcanzar el 100% de ocupación.",
    ],
    imperdibles: [
      "Concurso de Danzas Autóctonas en el Estadio Enrique Torres Belón.",
      "Gran Parada y Veneración a la Virgen de la Candelaria por el jirón Lima.",
      "Paseo en lancha a las islas flotantes de los Uros y la isla Taquile.",
      "Visita al mirador de Kuntur Wasi para una panorámica completa del lago Titicaca.",
    ],
    consejos: [
      "La altitud supera los 3.820 metros: el primer día tómalo con calma y bebe mate de coca o muña.",
      "Lleva ropa térmica para la noche y protector solar de alto factor para el mediodía.",
      "Lleva efectivo en moneda local para compras en ferias y puestos de comida tradicional.",
    ],
  },
  {
    id: "tarma-valle-flores",
    slug: "viaja-a-tarma-valle-de-las-flores",
    titulo: "Viaja a Tarma y vive la fiesta del Valle de las Flores: 7 planes imperdibles",
    extracto:
      "Conocida como «La Perla de los Andes», Tarma deslumbra con sus tapices florales, valles fértiles, gastronomía andina y clima primaveral a pocas horas de Lima.",
    categoria: "experiencia",
    lugar: "Junín",
    region: "Junín",
    fecha: "02/11/2026",
    tiempoLectura: "4 min de lectura",
    destacadoEnHome: false,
    destinoId: 114,
    foto: {
      archivo: "Pileta pricipal de tarma - panoramio.jpg",
      ruta: "b/bd",
      ancho: 819,
      alto: 614,
      autor: "Tours Centro Peru",
      licencia: "CC BY 3.0",
      url_licencia: "https://creativecommons.org/licenses/by/3.0",
      wikidata: "",
    },
    parrafos: [
      "A solo seis horas por carretera desde Lima, cruzando Ticlio, se abre un valle luminoso rodeado de andenes prehispánicos tapizados de flores: Tarma.",
      "Famosa en todo el Perú por sus tradicionales alfombras de flores durante Semana Santa y sus campos de claveles, gladiolos y rosas, la provincia combina historia colonial y naturaleza andina.",
      "Además de sus paisajes rurales, la gastronomía local conquista con el puchero tarmeño, el picante de cuy y el inigualable manjarblanco en olla de cobre.",
    ],
    imperdibles: [
      "Adentrarse en la Gruta de Huagapo, una de las cavernas más profundas de Sudamérica.",
      "Caminar por el pueblo artesanal de San Pedro de Cajas, cuna de tejedores de tapices.",
      "Visitar el Santuario del Señor de Muruhuay en Acobamba.",
      "Apreciar las vistas del valle desde el mirador de San Sebastián.",
    ],
    consejos: [
      "La ruta desde Lima asciende a más de 4.800 m en Ticlio antes de descender a los 3.050 m de Tarma: hidrátate bien.",
      "La mejor época floral abarca entre marzo y octubre, con días soleados y cielos despejados.",
    ],
  },
  {
    id: "chanchamayo-cataratas-cafe",
    slug: "que-hacer-en-chanchamayo-cataratas-cafe",
    titulo: "¿Qué hacer en Chanchamayo? 8 planes entre cataratas, café y naturaleza",
    extracto:
      "Selva central a tu alcance: cataratas cristalinas como Bayoz y Velo de la Novia, comunidades asháninkas, puentes colgantes y el mejor café de especialidad del Perú.",
    categoria: "naturaleza",
    lugar: "Junín",
    region: "Junín",
    fecha: "01/11/2026",
    tiempoLectura: "6 min de lectura",
    destacadoEnHome: false,
    destinoId: 852,
    foto: {
      archivo: "¡La catarata mas visitada en la Selva Central! Catarata Bayoz.jpg",
      ruta: "8/8a",
      ancho: 2048,
      alto: 1536,
      autor: "David Stanley",
      licencia: "CC BY 2.0",
      url_licencia: "https://creativecommons.org/licenses/by/2.0",
      wikidata: "",
    },
    parrafos: [
      "Chanchamayo es la puerta de entrada a la Amazonía peruana. En pocas horas de descenso desde la sierra central, el paisaje se transforma en una selva verde de neblina, ríos caudalosos y aroma a café tostado.",
      "Localidades como La Merced y San Ramón ofrecen la base perfecta para nadar bajo caídas de agua naturales, cruzar puentes colgantes y aprender sobre la cosecha de granos selectos.",
      "El ecoturismo se complementa con la visita a comunidades nativas asháninkas, donde es posible conocer de cerca sus cantos, danzas e historia ancestral.",
    ],
    imperdibles: [
      "Darse un baño refrescante en las pozas naturales de la Catarata Bayoz.",
      "Fotografiar la impresionante caída de 65 metros del Velo de la Novia.",
      "Degustar cafés premiados en cafeterías de especialidad en Villa Rica y La Merced.",
      "Navegar en bote por el río Perené y visitar la comunidad Marankiari Bajo.",
    ],
    consejos: [
      "Lleva repelente biodegradable y bloqueador solar para las caminatas en bosque tropical.",
      "Usa zapatillas con suela antideslizante para caminar sobre piedras mojadas cerca de las cascadas.",
    ],
  },
  {
    id: "huayllay-pasco-rural-tour",
    slug: "festival-rural-tour-huayllay-pasco",
    titulo: "Festival Rural Tour Huayllay: vive dos días de naturaleza y tradición en Pasco",
    extracto:
      "El bosque de piedras más alto y extenso del planeta te espera a más de 4.000 metros de altura para vivir escalada en roca, baños termales y rituales ancestrales.",
    categoria: "aventura",
    lugar: "Pasco",
    region: "Pasco",
    fecha: "28/10/2026",
    tiempoLectura: "4 min de lectura",
    destacadoEnHome: false,
    destinoId: 110,
    foto: {
      archivo: "Huayllay panoramic.jpg",
      ruta: "9/91",
      ancho: 1534,
      alto: 1151,
      autor: "Miguelcrux",
      licencia: "CC BY-SA 3.0",
      url_licencia: "http://creativecommons.org/licenses/by-sa/3.0/",
      wikidata: "Q2307812",
    },
    parrafos: [
      "Ubicado en la meseta de Bombón, a más de 4.300 metros sobre el nivel del mar, el Santuario Nacional de Huayllay alberga más de 4.000 formaciones rocosas gigantescas modeladas por la erosión volcánica.",
      "Durante el Festival Rural Tour, deportistas y viajeros de todo el país se congregan para participar en competencias de escalada en roca, carreras de chasquis y ceremonias de pago a la Pachamama.",
      "Tras la jornada en la puna, las aguas termales sulfurosas de La Calera ofrecen un descanso reconfortante a 60 °C de temperatura medicinal.",
    ],
    imperdibles: [
      "Hacer la ruta de trekking buscando figuras de piedra: el elefante, la cobra, el oso y la tortuga.",
      "Relajarse en las pozas termales de La Calera con vistas al cañón.",
      "Apreciar pinturas rupestres milenarias en abrigos rocosos protegidos.",
    ],
    consejos: [
      "Imprescindible ropa cortaviento y abrigo de montaña: en la noche la temperatura puede bajar de 0 °C.",
      "Aclimatarse al menos 24 horas previas en Tarma o Cerro de Pasco.",
    ],
  },
  {
    id: "ruta-tupac-amaru-cusco",
    slug: "la-ruta-de-tupac-amaru-ii-cusco",
    titulo:
      "La Ruta de Túpac Amaru II: Descubre la cuna de la libertad y los tesoros ocultos del Sur del Cusco",
    extracto:
      "Aventúrate más allá de la ciudad imperial y recorre los majestuosos paisajes del sur cusqueño. Conecta con la memoria de Túpac Amaru II y asómbrate con el puente Q'eswachaka.",
    categoria: "experiencia",
    lugar: "Cusco",
    region: "Cusco",
    fecha: "03/11/2026",
    tiempoLectura: "5 min de lectura",
    destinoId: 36,
    foto: {
      archivo: "Puente colonial Checacupe.jpg",
      ruta: "f/fc",
      ancho: 1920,
      alto: 1080,
      autor: "Cusco Colonial",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "",
    },
    parrafos: [
      "El Valle Sur del Cusco es una de las rutas con mayor densidad histórica y paisajística del Perú. Aquí nació y lideró la rebelión de 1780 José Gabriel Condorcanqui, Túpac Amaru II.",
      "Siguiendo la carretera hacia Puno, se descubren pueblos con templos coloniales decorados con murales barrocos andinos, lagunas serenas y puentes que desafían el tiempo.",
      "El punto cumbre del circuito es el puente Q'eswachaka, una joya de ingeniería incaica tejida con q'oya que la comunidad renueva ritualmente cada año sobre el río Apurímac.",
    ],
    imperdibles: [
      "Cruzar con respeto el puente colgante de Q'eswachaka suspendido a 15 metros del abismo.",
      "Contemplar el Circuito de las Cuatro Lagunas: Pomacanchi, Acopia, Asnacocha y Pampamarca.",
      "Visitar la iglesia de San Pedro Apóstol de Andahuaylillas, llamada la «Capilla Sixtina de América».",
      "Explorar los restos del templo de Wiracocha en Raqchi.",
    ],
    consejos: [
      "La ruta se puede hacer en un día completo o en dos días durmiendo en una casa rural de la zona.",
      "Disfruta de un almuerzo tradicional con trucha dorada fresca al borde de la laguna Pomacanchi.",
    ],
  },
  {
    id: "postres-peruanos-12-dulces",
    slug: "postres-peruanos-12-dulces-para-recorrer-el-peru",
    titulo: "Postres peruanos: 12 dulces para recorrer el Perú",
    extracto:
      "El dulce peruano no es uno solo ni se disfruta en todas partes igual. Descubre qué postres son típicos de cada región y los ingredientes que les dan su sabor característico.",
    categoria: "gastronomia",
    lugar: "Nacional",
    region: "Lima",
    fecha: "03/11/2026",
    tiempoLectura: "5 min de lectura",
    destinoId: 205,
    foto: {
      archivo: "Plaza Mayor de Lima-1.jpg",
      ruta: "5/54",
      ancho: 2048,
      alto: 1365,
      autor: "David Stanley",
      licencia: "CC BY 2.0",
      url_licencia: "https://creativecommons.org/licenses/by/2.0",
      wikidata: "Q2834571",
    },
    parrafos: [
      "La repostería tradicional peruana es fruto del mestizaje entre ingredientes nativos milenarios —como el camote, la calabaza, la yuca y el cacao— e influencias coloniales árabes, españolas y africanas.",
      "En Lima, los carretilleros nocturnos sirven picarones recién fritos en aros crocantes bañados con miel de chancaca, hojas de higo y cáscara de naranja.",
      "En Arequipa, el queso helado elaborado en bateas de madera con leche fresca, canela y coco seduce en cada plaza; mientras que en el norte el King Kong de manjar y piña es el obsequio infaltable.",
    ],
    imperdibles: [
      "Picarones limeños calientes en el Parque Kennedy o la Alameda Chabuca Granda.",
      "Queso helado en el Claustro de la Compañía de Arequipa.",
      "Suspiro a la limeña con oporto y merengue tostado.",
      "Tanta wawa cusqueña decorada con máscaras dulces en Todos los Santos.",
    ],
    consejos: [
      "Acompaña los postres con una infusión digestiva de hierbaluisa, muña o anís.",
      "En ferias y plazas locales los precios son muy accesibles y las porciones generosas.",
    ],
  },
  {
    id: "dia-todos-santos-lugares",
    slug: "dia-de-todos-los-santos-tradicion-peru",
    titulo: "Día de Todos los Santos: qué se celebra y 5 lugares para vivir esta tradición",
    extracto:
      "El aroma a tanta wawa recién horneada, altares llenos de color y melodías que celebran la memoria. Descubre qué se conmemora el 1 y 2 de noviembre en los Andes del Perú.",
    categoria: "festividades",
    lugar: "Nacional",
    region: "Cusco",
    fecha: "29/10/2026",
    tiempoLectura: "4 min de lectura",
    destinoId: 36,
    foto: {
      archivo: "Cusco, Sacsayhuamán - panoramio.jpg",
      ruta: "5/53",
      ancho: 4912,
      alto: 1920,
      autor: "gertrudis2010",
      licencia: "CC BY-SA 3.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/3.0",
      wikidata: "",
    },
    parrafos: [
      "El 1 y 2 de noviembre, las familias peruanas se reúnen para recordar a sus seres queridos en una festividad donde la memoria no se vive con tristeza, sino con música, flores y banquetes compartidos.",
      "En los cementerios andinos, las tumbas se adornan con coronas coloridas y se colocan mesas con las comidas y bebidas que más disfrutaban en vida los difuntos.",
      "La protagonista indiscutible de las mesas es la 'tanta wawa', un pan dulce ceremonial con forma de niño, caballo o muñeca coronado con caritas de pasta de azúcar.",
    ],
    imperdibles: [
      "Ferias de tanta wawa en la Plaza San Francisco del Cusco y en el mercado de Huamanga.",
      "Coronación de panes gigantes en el Valle del Mantaro (Huancayo).",
      "Celebraciones y pasacalles con músicos de arpa y violín en cementerios tradicionales.",
    ],
    consejos: [
      "Acércate con respeto a las ofrendas familiares en los cementerios públicos.",
      "Prueba las diferentes recetas de masa: algunas llevan anís estrella, chancaca y pasas.",
    ],
  },
  {
    id: "media-maraton-huacho",
    slug: "media-maraton-de-huacho-2026",
    titulo: "Media Maratón de Huacho 2026: corre por la Ruta de la Independencia",
    extracto:
      "Una carrera deportiva y turística frente al mar del norte chico. Recorre el malecón de Huacho, las lagunas costeras y celebra con la tradicional salchicha huachana.",
    categoria: "experiencia",
    lugar: "Lima",
    region: "Lima",
    fecha: "28/10/2026",
    tiempoLectura: "3 min de lectura",
    destinoId: 70,
    foto: {
      archivo: "Huacho Plaza de Armas de Huacho.jpg",
      ruta: "9/9e",
      ancho: 2048,
      alto: 1536,
      autor: "Municipalidad de Huacho",
      licencia: "CC BY 3.0",
      url_licencia: "https://creativecommons.org/licenses/by/3.0",
      wikidata: "",
    },
    parrafos: [
      "El Norte Chico de Lima combina historia libertaria, brisa marina y una tradición deportiva que convoca a miles de corredores en la Media Maratón de Huacho.",
      "El circuito costero bordea los acantilados de la playa Hornillos y la bahía de Carquín, ofreciendo una vista panorámica del Pacífico durante toda la competencia.",
      "Tras la meta, el festejo gastronómico es obligado: pan crujiente con salchicha huachana, cebiche de pato y chicha de jora en los restaurantes del malecón.",
    ],
    imperdibles: [
      "Pasear por el Malecón Rocca y el Balcón de Huaura, donde don José de San Martín proclamó la independencia.",
      "Recorrer la albufera de Medio Mundo y observar aves migratorias marinas.",
      "Degustar salchicha huachana artesanal en los mercados locales.",
    ],
    consejos: [
      "Huacho está a solo 2.5 horas de Lima por la Panamericana Norte: ideal para una escapada de fin de semana.",
      "Si corres, lleva calzado adecuado para asfalto plano con buena amortiguación.",
    ],
  },
  {
    id: "rutas-misticas-selva-costa",
    slug: "rutas-misticas-mitos-y-leyendas",
    titulo: "¡Rutas místicas! Descubre la selva y la costa norte a través de sus mitos y leyendas",
    extracto:
      "Navega por ríos legendarios, intérnate en bosques vírgenes y recorre valles desérticos junto al mar donde los mitos de la luna y el chullachaqui cobran vida.",
    categoria: "experiencia",
    lugar: "Nacional",
    region: "San Martín",
    fecha: "27/10/2026",
    tiempoLectura: "5 min de lectura",
    destinoId: 101,
    foto: {
      archivo: "Bella Durmiente TM-Peru-1.jpg",
      ruta: "f/f3",
      ancho: 2048,
      alto: 1536,
      autor: "Yagamichega",
      licencia: "CC BY 3.0",
      url_licencia: "https://creativecommons.org/licenses/by/3.0",
      wikidata: "Q1974467",
    },
    parrafos: [
      "El Perú es tierra de leyendas vivas. En los ríos amazónicos, las historias del Chullachaqui y el bufeo colorado no son simples cuentos infantiles: son guardianes del respeto a la selva y a sus árboles milenarios.",
      "En la costa norte, los santuarios de adobe de los mochicas y chimúes revelan templos dedicados a la luna y al dios Naylamp, señor que llegó desde el mar para fundar un imperio.",
      "Viajar por estas rutas con guías locales permite conectar con la cosmovisión andino-amazónica de una manera profunda e inolvidable.",
    ],
    imperdibles: [
      "Navegar la laguna Azul en Sauce (San Martín) y escuchar historias de sirenas locales.",
      "Visitar las pirámides de Túcume y el Museo de las Tumbas Reales de Sipán.",
      "Conocer el bosque de algarrobos de Pómac bajo la luna llena.",
    ],
    consejos: [
      "Escucha siempre las advertencias y rituales de agradecimiento de las comunidades locales antes de internarte en bosques vírgenes.",
    ],
  },
];
