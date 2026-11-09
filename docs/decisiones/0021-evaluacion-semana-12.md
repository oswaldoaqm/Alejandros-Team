# 0021 · Cómo se evalúa lo que propone el motor

**Fecha:** 20 de octubre de 2026 · **Estado:** vigente · Hace la evaluación que dejó pendiente la semana 6 ([`ModelSelection.md`](../../deliveries/week06/ModelSelection.md), §8.5), con lo que muestra el producto: tres viajes

## Contexto

La semana 6 dejó sin verdad de campo la recomendación, es decir, qué zonas propone el motor: hacía falta un conjunto de consultas calificado a mano por los cuatro, con su acuerdo medido por kappa de Fleiss, y sobre él Precision@5, nDCG@10 y MRR, más cobertura del catálogo y novedad. El producto propone tres viajes, no cinco ni diez. Y el valor de una parada, 1, 2, 6 o 24 según su jerarquía y la cuarta parte si no es de lo que se pidió, es un supuesto «todavía sin calibrar» ([contrato](../CONTRATO.md)). Al preparar las consultas se vio por qué importa: para un fin de semana de playa desde Lima, el motor propone Nasca, que no tiene playas, porque las Líneas, de jerarquía 4, valen 6 aunque no sean de lo pedido, y una playa de jerarquía 2 vale 2.

## Decisión

- **40 consultas escritas a mano** ([`evaluacion/consultas.csv`](../../evaluacion/consultas.csv)), cada una con quién viaja: 15 orígenes, 16 desde Lima; de 2 a 10 días; los doce meses; cada interés al menos dos veces y cinco sin ninguno; con presupuesto, altitud máxima, «Solo por tierra», «Sorpréndeme» y dos con fecha.
- **Tres sistemas, con hasta tres zonas cada uno:**
  - **el motor**, el desplegado;
  - **la guía**, la línea de base: entre las zonas que caben con las mismas reglas del motor, las tres más conocidas por lo que se pidió, con la misma escala de jerarquías y sin mirar el mes, el presupuesto, lo que alcanza a verse en esos días ni lo poco visitado ([`evaluacion/linea_base.py`](../../evaluacion/linea_base.py));
  - **la variante**, el motor con la raíz cuadrada de la calidad en el puntaje, que reparte más los viajes entre las zonas ([`evaluacion/variante.py`](../../evaluacion/variante.py)). No se despliega: es para decidir con datos si conviene. Hasta el 5 de noviembre era otra; ver abajo.
- **Cada zona propuesta se califica una vez**, la proponga uno o varios: 196 viajes con los datos `2026.11.1` (185 con los `2026.10.8`). El viaje a una zona es el que arma el motor desplegado, para todos, así que lo único que se compara es qué zonas se proponen y en qué orden.
- **La escala:** 2 si se le recomendaría tal cual a esa persona, 1 si podría servirle con reparos, 0 si no encaja ([`anotar.md`](../evaluacion/anotar.md)). Califican los cuatro, por separado, sin saber de qué sistema sale cada viaje, en un orden mezclado y fijo ([`evaluacion/kit.py`](../../evaluacion/kit.py)).
- **Lo que se calcula,** fijado antes de calificar:
  - el acuerdo, con el kappa de Fleiss, y el alfa de Krippendorff ordinal, porque 2, 1 y 0 tienen orden. Con kappa bajo 0,4 las cifras se dan igual, como no concluyentes, y se revisan con el equipo los viajes de más desacuerdo;
  - la nota de cada viaje, la media de las cuatro;
  - por sistema: nDCG@3 con esa nota, P@3 con «se lo recomendarían», que es una media de 1,5 o más, MRR con el mismo umbral, y cuántos de sus tres viajes no encajan, con una media bajo 0,5;
  - la diferencia entre sistemas, consulta por consulta, con un intervalo de 95 % por bootstrap sobre las 40 y la prueba de Wilcoxon;
  - la cobertura, las zonas distintas que propone cada uno en las 40 consultas, y la novedad, la parte de sus viajes fuera del circuito de Lima y Cusco.
- **La usabilidad:** cinco personas fuera del equipo, cinco tareas y el SUS ([`usabilidad.md`](../evaluacion/usabilidad.md)).

## Alternativas descartadas

- **Lo más conocido sin mirar los intereses** como línea de base: para quien pide playa propone el Cusco, Puno y Huaraz. Le gana cualquier cosa que mire los intereses, y ganarle no diría nada.
- **Solo el motor, sin línea de base:** diría cuán buenos son sus viajes, no si el puntaje aporta.
- **P@5 y nDCG@10:** el producto muestra tres viajes.
- **Que cada sistema arme su propio viaje a cada zona:** la misma zona saldría dos veces con planes distintos, y la diferencia de planes se mezclaría con la de zonas.
- **Cambiar el valor de lo no pedido antes de evaluar:** se evaluaría algo que nadie probó en la app, y no habría con qué comparar.

## Consecuencias

- **Se mide qué zonas se proponen,** no cada plan. Que el motor desplegado arme el viaje de los tres sistemas favorece a la guía: sus zonas llevan el plan del motor. Lo que la variante cambiaría dentro de cada viaje, más paradas de lo pedido, se mide aparte y sin calificaciones.
- **Quienes califican hicieron el producto:** pueden reconocer el estilo del motor. El orden mezclado y la clave cerrada lo atenúan, no lo quitan, y el informe lo dice.
- **Son 40 consultas hechas a mano,** pensadas para cubrir el producto: sirven para comparar sistemas sobre las mismas consultas, no para estimar cómo le va con cualquier consulta.
- **El kit es de los datos con que se arma y del contrato 1.7:** se arma con lo desplegado, y si el motor cambia, las calificaciones siguen valiendo para esa versión, no para la nueva. El del 5 de noviembre es de los datos `2026.11.1`.

## Cambio del 5 de noviembre: otra variante

La variante de la décima parte coincidía con el motor en 110 de sus 120 propuestas, y en 30 de las 40 consultas proponía las mismas tres zonas: calificarla no iba a decir casi nada. Lo que sí se ve en el uso es lo contrario, que el motor propone casi siempre las mismas zonas: en la rejilla de 1 152 consultas de la semana 10, los diez polos más propuestos se llevaban el 80 % de los viajes. La variante pasa a ser la raíz cuadrada de la calidad, que acorta la distancia entre las mejores zonas y le da más peso a la novedad. Con los datos `2026.11.1`, comparte con el motor 100 de sus 120 propuestas, y en 22 de las 40 consultas propone las mismas tres zonas. En las 40, propone 33 zonas distintas (el motor, 29), el 80 % de sus viajes va fuera del circuito de Lima y Cusco (el motor, 75 %) y su novedad media es 0,46 (el motor, 0,43). En la rejilla de 1 152 consultas (`python -m evaluacion.auditoria --variante`), las diez zonas más propuestas se llevan el 76 % de los viajes con la variante y el 80 % con el motor, y salen 66 zonas distintas contra 56; Miraflores baja del 19 al 11 %. Reparte algo más, pero tres de cada cuatro viajes siguen yendo a diez zonas. La diferencia con el motor sale de 18 consultas: el kit solo la verá si es grande, y así se dirá en el informe. El caso de la playa que motivó la variante anterior se mide aparte, sin calificaciones.
