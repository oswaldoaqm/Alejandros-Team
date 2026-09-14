# Justificación de Scripts (Data Engineering Pipeline)

Esta carpeta contiene los scripts ejecutados durante la Semana 6 para llevar los datos crudos a un estado 100% procesado para el Machine Learning.

1. **`scraper_mincetur.py`**:
   * *Justificación:* Extrae la `Jerarquía Oficial` y otros datos leyendo directamente el código HTML de las más de 4,900 URLs del MINCETUR. Asegura que el algoritmo priorice destinos oficiales reales.
2. **`clean_impute_dataset.py`**:
   * *Justificación:* Al detectar que el HTML de la web gubernamental contiene ruido (tablas mal formateadas), este script aplica *Rule-Based Imputation* para curar variables como el `Tipo de Ingreso` basándose en la jerarquía, garantizando un dataset categórico impecable sin nulos.
3. **`fetch_climate_history.py`**:
   * *Justificación:* Se conecta a la API de Open-Meteo y extrae 10 años exactos de historia meteorológica mensual por Región. Es el corazón de la Analítica Predictiva que solicitó el profesor para pronosticar los riesgos de lluvia en lugar de usar reglas estáticas.
4. **`discretize_climate.py`**:
   * *Justificación:* Transforma las variables continuas de lluvia y temperatura en cajas categóricas (ej. *1_Seguro, 3_Peligro*). Esta técnica de *Binning* optimiza la velocidad y precisión del Recomendador Espacio-Temporal.
5. **`generate_commerce_data.py`**:
   * *Justificación:* Crea un dataset sintético de eventos y ferias para resolver el problema de recolección dinámica de datos (Two-Sided Marketplace). Permite simular cómo la app inyectaría anuncios temporales en la ruta del usuario.
