# 0021 · Cómo se evalúa lo que propone el motor

**Fecha:** 20 de octubre de 2026 · **Estado:** vigente · Hace la evaluación que dejó pendiente la semana 6 ([`ModelSelection.md`](../../deliveries/week06/ModelSelection.md), §8.5), con lo que muestra el producto: tres viajes

## Contexto

La semana 6 dejó sin verdad de campo la recomendación, es decir, qué zonas propone el motor: hacía falta un conjunto de consultas calificado a mano por los cuatro, con su acuerdo medido por kappa de Fleiss, y sobre él Precision@5, nDCG@10 y MRR, más cobertura del catálogo y novedad. El producto propone tres viajes, no cinco ni diez. Y el valor de una parada, 1, 2, 6 o 24 según su jerarquía y la cuarta parte si no es de lo que se pidió, es un supuesto «todavía sin calibrar» ([contrato](../CONTRATO.md)). Al preparar las consultas se vio por qué importa: para un fin de semana de playa desde Lima, el motor propone Nasca, que no tiene playas, porque las Líneas, de jerarquía 4, valen 6 aunque no sean de lo pedido, y una playa de jerarquía 2 vale 2.

## Decisión

- **40 consultas escritas a mano** ([`evaluacion/consultas.csv`](../../evaluacion/consultas.csv)), cada una con quién viaja: 15 orígenes, 16 desde Lima; de 2 a 10 días; los doce meses; cada interés al menos dos veces y cinco sin ninguno; con presupuesto, altitud máxima, «Solo por tierra», «Sorpréndeme» y dos con fecha.
- **Tres sistemas, con hasta tres zonas cada uno:**
  - **el motor**, el desplegado;
  - **la guía**, la línea de base: entre las zonas que caben con las mismas reglas del motor, las tres más conocidas por lo que se pidió, con la misma escala de jerarquías y sin mirar el mes, el presupuesto, lo que alcanza a verse en esos días ni lo poco visitado ([`evaluacion/linea_base.py`](../../evaluacion/linea_base.py));
  - **la variante**, el motor con la décima parte en vez de la cuarta para lo que no es de lo pedido ([`evaluacion/variante.py`](../../evaluacion/variante.py)). No se despliega: es para decidir con datos si conviene.
- **Cada zona propuesta se califica una vez**, la proponga uno o varios: 185 viajes. El viaje a una zona es el que arma el motor desplegado, para todos, así que lo único que se compara es qué zonas se proponen y en qué orden.
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
- **El kit es de los datos `2026.10.8` y del contrato 1.7:** se arma con lo desplegado, y si el motor cambia, las calificaciones siguen valiendo para esa versión, no para la nueva.
