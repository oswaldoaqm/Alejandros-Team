// Festividades y eventos destacados del calendario oficial de MINCETUR en DreemGO.
// Se seleccionan de forma dinámica según la fecha actual del usuario para garantizar
// que siempre se muestren festividades en curso o próximas a celebrarse.

import type { Foto } from "../fotos";

export interface FestividadMes {
  id: string;
  titulo: string;
  extracto: string;
  descripcionDetallada: string;
  actividades: string[];
  categoria: "Festividades" | "Eventos";
  diaRango: string;
  mesRango: string;
  fechasTexto: string;
  fechaInicio: string; // Formato AAAA-MM-DD para filtrado dinámico
  fechaFin: string; // Formato AAAA-MM-DD para filtrado dinámico
  lugar: string;
  region: string;
  destinoNombre: string;
  destinoId: number;
  foto: Foto;
}

export const TODAS_LAS_FESTIVIDADES: FestividadMes[] = [
  // ── 1. Primera quincena de noviembre ─────────────────────────────────────
  {
    id: "festival-salchicha-huachana",
    titulo: "Festival de la Salchicha Huachana",
    extracto:
      "¡Huacho rinde homenaje a su emblemático embutido artesanal con degustaciones gastronómicas, concursos de cocina tradicional y presentaciones de música criolla!",
    descripcionDetallada:
      "El Festival de la Salchicha Huachana celebra la tradición culinaria viva del norte chico de Lima. En la Plaza de Armas de Huacho, maestros salchicheros tradicionales muestran la elaboración artesanal de este ícono gastronómico de color achiotado, acompañado de degustaciones, concursos al mejor desayuno huachano, ferias de productos del valle de Huaura y estampas folclóricas.",
    actividades: [
      "Gran feria gastronómica y degustación popular de salchicha huachana",
      "Concurso culinario del mejor desayuno tradicional huachano",
      "Espectáculos artísticos de marinera norteña y música criolla en vivo",
      "Feria agropecuaria de productos locales del valle de Huaura",
    ],
    categoria: "Eventos",
    diaRango: "1-7",
    mesRango: "NOV.",
    fechasTexto: "Del 1 al 7 de noviembre",
    fechaInicio: "2026-11-01",
    fechaFin: "2026-11-07",
    lugar: "Huacho",
    region: "Lima",
    destinoNombre: "Huacho y alrededores",
    destinoId: 70,
    foto: {
      archivo: "Huacho Plaza de Armas de Huacho.jpg",
      ruta: "9/9e",
      ancho: 1480,
      alto: 970,
      autor: "Xauxa Håkan Svensson",
      licencia: "CC BY-SA 3.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/3.0",
      wikidata: "",
    },
  },
  {
    id: "festival-orquidea-moyobamba",
    titulo: "Festival de la Orquídea de Moyobamba",
    extracto:
      "¡La 'Ciudad de las Orquídeas' deslumbra con la mayor exhibición botánica de la Amazonía peruana, circuitos ecoturísticos, ferias de artesanía y danzas selváticas!",
    descripcionDetallada:
      "Cada noviembre, Moyobamba celebra su título de Capital de las Orquídeas del Perú con su afamado Festival de la Orquídea. Viveros, botánicos y comunidades locales exhiben ejemplares únicos de las más de 3,500 variedades nativas de la región San Martín, combinando la feria botánica con rutas ecoturísticas a los baños termales de San Mateo, ferias de café y cacao de origen y alegres pandilladas selváticas.",
    actividades: [
      "Exposición botánica internacional de orquídeas nativas y exóticas",
      "Rutas ecoturísticas guiadas por orquidearios y reservas naturales",
      "Feria de artesanía amazónica, café de especialidad y cacao fino",
      "Pandillada moyobambina y danzas folclóricas de la selva alta",
    ],
    categoria: "Eventos",
    diaRango: "1-7",
    mesRango: "NOV.",
    fechasTexto: "Del 1 al 7 de noviembre",
    fechaInicio: "2026-11-01",
    fechaFin: "2026-11-07",
    lugar: "Moyobamba",
    region: "San Martín",
    destinoNombre: "Moyobamba y Alto Mayo",
    destinoId: 86,
    foto: {
      archivo: "Moyobamba, Peru, 2018.jpg",
      ruta: "1/10",
      ancho: 3000,
      alto: 2000,
      autor: "Aleksei M.",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "Q285672",
    },
  },
  {
    id: "escenificacion-quespiwanca-tinkuy",
    titulo: "Escenificación Quespiwanca Tinkuy",
    extracto:
      "¡El Valle Sagrado revive el esplendor del inca Huayna Cápac con la escenificación teatral del Tinkuy en el palacio de Quespiwanca, música ancestral y danzas cusqueñas!",
    descripcionDetallada:
      "La Escenificación Quespiwanca Tinkuy se realiza cada 5 de noviembre en Urubamba, en el corazón del Valle Sagrado de los Incas. La festividad conmemora el esplendor del palacio campestre del inca Huayna Cápac con una monumental puesta en escena teatral donde cientos de danzantes y actores representan el encuentro (tinkuy) de las panacas reales, el tributo al sol y rituales sagrados andinos.",
    actividades: [
      "Monumental escenificación histórica incaica en el Palacio de Quespiwanca",
      "Ceremonia ancestral de ofrenda a la Pachamama y encuentro de panacas reales",
      "Pasacalle de danzas autóctonas del Cusco y música tradicional con pututos",
      "Feria artesanal y muestra de gastronomía andina tradicional en Urubamba",
    ],
    categoria: "Eventos",
    diaRango: "5",
    mesRango: "NOV.",
    fechasTexto: "5 de noviembre",
    fechaInicio: "2026-11-05",
    fechaFin: "2026-11-05",
    lugar: "Urubamba",
    region: "Cusco",
    destinoNombre: "Urubamba y Valle Sagrado",
    destinoId: 173,
    foto: {
      archivo: "Urubambatown.jpg",
      ruta: "4/46",
      ancho: 1600,
      alto: 1200,
      autor: "Adam Broadhead",
      licencia: "CC BY-SA 3.0",
      url_licencia: "http://creativecommons.org/licenses/by-sa/3.0/",
      wikidata: "Q2304483",
    },
  },
  {
    id: "patronal-san-martin-tours-sechura",
    titulo: "Festividad Patronal en Honor a San Martín de Tours",
    extracto:
      "La festividad patronal de Sechura reúne a miles de devotos y visitantes con danzas de negritos, ferias gastronómicas de cebiche norteño y celebraciones costumbristas.",
    descripcionDetallada:
      "La Festividad Patronal en Honor a San Martín de Tours es una de las expresiones de fe y tradición más vivas de la costa norte del Perú. Sechura se viste de gala con las tradicionales danzas de los 'Negritos de Sechura', pasacalles de bandas de músicos, quema de castillos pirotécnicos y multitudinarias ferias donde se degusta el auténtico cebiche sechurano y la chicha de jora.",
    actividades: [
      "Danza de los Negritos de Sechura con coloridas vestimentas y cascabeles",
      "Solemne procesión del Santo Patrón por la histórica Plaza de Armas",
      "Degustación de cebiche de conchas negras y gastronomía marina",
      "Festival de bandas de músicos y quema de vistosos fuegos artificiales",
    ],
    categoria: "Festividades",
    diaRango: "5-12",
    mesRango: "NOV.",
    fechasTexto: "Del 5 al 12 de noviembre",
    fechaInicio: "2026-11-05",
    fechaFin: "2026-11-12",
    lugar: "Sechura",
    region: "Piura",
    destinoNombre: "Sechura y Piura",
    destinoId: 125,
    foto: {
      archivo: "Piura Plaza de Armas.jpg",
      ruta: "5/50",
      ancho: 2032,
      alto: 1354,
      autor: "Alfredobi",
      licencia: "Public domain",
      url_licencia: "",
      wikidata: "Q223966",
    },
  },

  // ── 2. Segunda quincena de noviembre ─────────────────────────────────────
  {
    id: "festival-camu-camu-iquitos",
    titulo: "Festival del Camu Camu",
    extracto:
      "¡Iquitos rinde homenaje al superfruto amazónico con ferias de gastronomía y coctelería selvática, concursos de cosecha y música en el malecón!",
    descripcionDetallada:
      "El Festival del Camu Camu es una de las celebraciones de la agrobiodiversidad más coloridas de Loreto. En la ciudad fluvial de Iquitos, productores y chefs amazónicos exhiben la riqueza nutricional de este fruto de los várzeas del río Amazonas, con catas de postres selváticos, ferias agroecológicas, concursos al racimo más grande y presentaciones musicales ribereñas.",
    actividades: [
      "Feria gastronómica de postres y coctelería amazónica a base de camu camu",
      "Rutas fluviales a comunidades nativas y plantaciones ribereñas",
      "Concurso regional de innovación culinaria y productos transformados",
      "Presentaciones de danzas amazónicas y música típica de Loreto",
    ],
    categoria: "Eventos",
    diaRango: "13-15",
    mesRango: "NOV.",
    fechasTexto: "Del 13 al 15 de noviembre",
    fechaInicio: "2026-11-13",
    fechaFin: "2026-11-15",
    lugar: "Iquitos",
    region: "Loreto",
    destinoNombre: "Iquitos y el Río Amazonas",
    destinoId: 150,
    foto: {
      archivo: "Iquitos en la noche.JPG",
      ruta: "e/e7",
      ancho: 1024,
      alto: 521,
      autor: "Percy Meza",
      licencia: "CC BY-SA 3.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/3.0",
      wikidata: "Q383734",
    },
  },
  {
    id: "festival-apicola-illimo",
    titulo: "Festival Apícola de Íllimo",
    extracto:
      "¡La 'Tierra del Tumi de Oro' celebra su centenaria tradición apícola en los bosques secos de Lambayeque con degustaciones de miel de algarrobo y ferias artesanales!",
    descripcionDetallada:
      "El distrito de Íllimo, cuna de la cultura Lambayeque y tierra de orfebres prehispánicos, celebra en noviembre el Festival Apícola. Familias productoras de los bosques de algarrobo y sapote exponen mieles puras, propóleos y derivados, acompañados de ferias de platos típicos como el cabrito a la norteña y danzas costumbristas.",
    actividades: [
      "Feria de mieles silvestres de algarrobo y productos de la colmena",
      "Visitas a apiarios ecológicos en los bosques secos de Pómac",
      "Muestra gastronómica de comida típica lambayecana y chicha de jora",
      "Pasacalles de marinera tradicional y música de bandas de pueblo",
    ],
    categoria: "Eventos",
    diaRango: "20-22",
    mesRango: "NOV.",
    fechasTexto: "Del 20 al 22 de noviembre",
    fechaInicio: "2026-11-20",
    fechaFin: "2026-11-22",
    lugar: "Íllimo",
    region: "Lambayeque",
    destinoNombre: "Ferreñafe e Íllimo",
    destinoId: 25,
    foto: {
      archivo: "Parque Principal de Illimo.JPG",
      ruta: "0/06",
      ancho: 2048,
      alto: 1536,
      autor: "Jorge cherres",
      licencia: "CC BY-SA 3.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/3.0",
      wikidata: "Q17073502",
    },
  },

  // ── 3. Diciembre ──────────────────────────────────────────────────────────
  {
    id: "patronal-virgen-inmaculada-juli",
    titulo: "Festividad Virgen de la Inmaculada Concepción",
    extracto:
      "¡La 'Pequeña Roma de América' a orillas del lago Titicaca conmemora su festividad con danzas autóctonas de siku-morenos, trajes de luces y solemne procesión!",
    descripcionDetallada:
      "Juli, conocida históricamente como la Pequeña Roma de América por sus templos barrocos mestizos, celebra en diciembre la Festividad de la Virgen de la Inmaculada Concepción. La plaza central se llena de comparsas de morenadas, caporales y sikuris a más de 3,800 m s.n.m., con procesión junto al lago sagrado.",
    actividades: [
      "Solemne procesión de la Virgen por los templos virreinales de Juli",
      "Gran concurso y pasacalle de danzas con trajes de luces y sikuris",
      "Feria artesanal textil de alpaca y cerámica tradicional puneña",
      "Muestra de gastronomía del altiplano y trucha del Titicaca",
    ],
    categoria: "Festividades",
    diaRango: "6-9",
    mesRango: "DIC.",
    fechasTexto: "Del 6 al 9 de diciembre",
    fechaInicio: "2026-12-06",
    fechaFin: "2026-12-09",
    lugar: "Juli",
    region: "Puno",
    destinoNombre: "Juli y Lago Titicaca",
    destinoId: 140,
    foto: {
      archivo: "Juli 1.jpg",
      ruta: "7/70",
      ancho: 2592,
      alto: 1944,
      autor: "Ed88",
      licencia: "CC BY-SA 3.0",
      url_licencia: "http://creativecommons.org/licenses/by-sa/3.0/",
      wikidata: "Q2588438",
    },
  },
  {
    id: "patronal-virgen-de-la-puerta-otuzco",
    titulo: "Fiesta Patronal de la Virgen de la Puerta",
    extracto:
      "¡Otuzco celebra a la 'Mamita de la Puerta', Patrona del Norte del Perú, con su emocionante bajada del altar, bandas de músicos, fuegos artificiales y devoción multitudinaria!",
    descripcionDetallada:
      "La Fiesta Patronal de la Virgen de la Puerta en Otuzco es una de las manifestaciones de fe más imponentes del Perú, declarada Patrimonio Cultural de la Nación. Durante los días centrales, miles de fieles y peregrinos ascienden a la sierra liberteña para presenciar la emotiva bajada de la sagrada imagen desde lo alto de su santuario hasta la multitud congregada en la plaza, entre cuadrillas de danzas de gitanos, negritos y fuegos artificiales.",
    actividades: [
      "Emotiva y tradicional bajada de la Virgen de la Puerta desde el santuario",
      "Pasacalles de danzas tradicionales: Negritos, Gitanas y Diablos de Otuzco",
      "Gran quema de vistosos castillos pirotécnicos en la Plaza Mayor",
      "Feria gastronómica con el tradicional jamón serrano y panes de trigo",
    ],
    categoria: "Festividades",
    diaRango: "15-17",
    mesRango: "DIC.",
    fechasTexto: "Del 15 al 17 de diciembre",
    fechaInicio: "2026-12-15",
    fechaFin: "2026-12-17",
    lugar: "Otuzco",
    region: "La Libertad",
    destinoNombre: "Otuzco y alrededores",
    destinoId: 108,
    foto: {
      archivo: "Cathedral in Otuzco.jpg",
      ruta: "3/3f",
      ancho: 2304,
      alto: 1728,
      autor: "Wikiperuvian",
      licencia: "Public domain",
      url_licencia: "",
      wikidata: "Q3056421",
    },
  },
  {
    id: "navidad-chacasina",
    titulo: "Navidad Chacasina y Danza de Pastores",
    extracto:
      "¡En el corazón del Callejón de Conchucos, Chacas celebra la Navidad andina con danzas de pastores, guitarras, fuegos pirotécnicos y tallados en madera!",
    descripcionDetallada:
      "La Navidad en Chacas combina la profunda fe andina con la tradición artesanal de los talleres Don Bosco. En la histórica plaza andina con balcones tallados, cuadrillas de niños y jóvenes ataviados con trajes tradicionales bailan la danza de los 'Pastores de Chacas', acompañados por violines y arpas andinas.",
    actividades: [
      "Danza tradicional de los Pastores de Chacas frente a la iglesia matriz",
      "Recorrido por los célebres talleres de tallado en madera y vitrales",
      "Misa de gallo en quechua y procesión navideña por calles empedradas",
      "Degustación de chocolate caliente con panetón artesanal chacasino",
    ],
    categoria: "Festividades",
    diaRango: "24-28",
    mesRango: "DIC.",
    fechasTexto: "Del 24 al 28 de diciembre",
    fechaInicio: "2026-12-24",
    fechaFin: "2026-12-28",
    lugar: "Chacas",
    region: "Áncash",
    destinoNombre: "Chacas y Callejón de Conchucos",
    destinoId: 244,
    foto: {
      archivo: "Chacas-cascohistórico.jpg",
      ruta: "d/da",
      ancho: 960,
      alto: 639,
      autor: "Lamder",
      licencia: "CC BY-SA 4.0",
      url_licencia: "https://creativecommons.org/licenses/by-sa/4.0",
      wikidata: "Q2423013",
    },
  },

  // ── 4. Enero y Febrero ───────────────────────────────────────────────────
  {
    id: "festividad-virgen-de-la-candelaria-puno",
    titulo: "Festividad de la Virgen de la Candelaria",
    extracto:
      "¡La mayor fiesta del folclore de América reúne en Puno a más de cien mil danzantes y músicos de morenadas, diabladas y trajes de luces junto al Titicaca!",
    descripcionDetallada:
      "La Festividad de la Virgen de la Candelaria en Puno, Patrimonio Cultural Inmaterial de la Humanidad por la UNESCO, es el espectáculo cultural y religioso más monumental del continente. Durante dos semanas continuas, la ciudad del altiplano vibra con los multitudinarios concursos en el estadio Enrique Torres Belón, la veneración de la 'Mamita Candelaria' y los pasacalles de diabladas, caporales y morenadas.",
    actividades: [
      "Concurso de danzas autóctonas y trajes de luces con más de 100 mil artistas",
      "Solemne procesión de la Virgen de la Candelaria por las calles de Puno",
      "Gran parada folclórica y veneración multitudinaria día y noche",
      "Feria artesanal de máscaras de diablada y trajes bordados a mano",
    ],
    categoria: "Festividades",
    diaRango: "21-17",
    mesRango: "ENE. FEB.",
    fechasTexto: "Del 21 de enero al 17 de febrero",
    fechaInicio: "2027-01-21",
    fechaFin: "2027-02-17",
    lugar: "Puno",
    region: "Puno",
    destinoNombre: "Puno y Lago Titicaca",
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
  },
];

function fechaACadena(fecha: Date): string {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${anio}-${mes}-${dia}`;
}

/**
 * Selecciona dinámicamente las 4 festividades más inmediatas y relevantes para la fecha
 * dada (o hoy por defecto). Las que ya terminaron quedan excluidas automáticamente,
 * dando paso a las siguientes conforme avanzan los días.
 */
export function obtenerFestividadesVivas(fechaReferencia: Date = new Date()): FestividadMes[] {
  const hoyStr = fechaACadena(fechaReferencia);

  // Eventos que aún no han terminado (activos hoy o por comenzar en el futuro)
  const vigentes = TODAS_LAS_FESTIVIDADES.filter((f) => f.fechaFin >= hoyStr);

  // Ordenar: primero los que están activos HOY (0), luego los futuros (1) por fecha de inicio
  const ordenados = [...vigentes].sort((a, b) => {
    const aActivo = a.fechaInicio <= hoyStr && hoyStr <= a.fechaFin ? 0 : 1;
    const bActivo = b.fechaInicio <= hoyStr && hoyStr <= b.fechaFin ? 0 : 1;
    if (aActivo !== bActivo) return aActivo - bActivo;
    return a.fechaInicio.localeCompare(b.fechaInicio);
  });

  const seleccionados = ordenados.slice(0, 4);

  // Si quedan menos de 4 en lo que resta del año, completamos con el catálogo para mantener la cuadrícula
  if (seleccionados.length < 4) {
    const restantes = TODAS_LAS_FESTIVIDADES.filter((f) => !seleccionados.some((s) => s.id === f.id));
    seleccionados.push(...restantes.slice(0, 4 - seleccionados.length));
  }

  return seleccionados;
}

/** Lista viva para el momento actual (mantiene compatibilidad directa) */
export const FESTIVIDADES_MES: FestividadMes[] = obtenerFestividadesVivas();
