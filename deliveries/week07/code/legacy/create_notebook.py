import json

notebook_structure = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# DreemGO - Motor Predictivo y de Recomendación\n",
    "### Fase de Experimentación (Semana 6/7)\n",
    "Este notebook demuestra los dos pilares predictivos propuestos para el Data Product:\n",
    "1. **Predicción de Viabilidad Climática:** Análisis de 10 años de series de tiempo para estimar la seguridad del viaje.\n",
    "2. **Recomendación Comercial Dinámica:** Inyección de ferias y eventos temporales en base a las fechas de viaje."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from datetime import datetime\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "# Configuración visual\n",
    "sns.set_theme(style=\"darkgrid\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Análisis y Predicción Climática (Forecasting Espacial)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cargar datos históricos del clima\n",
    "df_clima = pd.read_csv('../data/historial_clima_regiones.csv', sep=';')\n",
    "df_clima['MES'] = df_clima['MES'].astype(int)\n",
    "print(f\"Registros climáticos cargados: {len(df_clima)}\")\n",
    "df_clima.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# EDA: Comportamiento histórico de las lluvias en CUSCO (La base para predecir)\n",
    "df_cusco = df_clima[df_clima['REGION'] == 'CUSCO']\n",
    "\n",
    "plt.figure(figsize=(10, 5))\n",
    "sns.boxplot(data=df_cusco, x='MES', y='PRECIPITACION_TOTAL_MM', palette='Blues')\n",
    "plt.title('Distribución Histórica de Lluvias en CUSCO (2014-2023)')\n",
    "plt.ylabel('Precipitación Total (mm)')\n",
    "plt.xlabel('Mes')\n",
    "plt.show()\n",
    "\n",
    "print(\"Insight: El modelo predictivo penalizará severamente los viajes en Enero, Febrero y Marzo.\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "def calcular_score_viabilidad(region, mes_viaje):\n",
    "    \"\"\"\n",
    "    Motor predictivo simplificado basado en promedios estadísticos históricos.\n",
    "    Retorna un score del 0% al 100% de viabilidad para viajar.\n",
    "    \"\"\"\n",
    "    df_filtro = df_clima[(df_clima['REGION'] == region) & (df_clima['MES'] == mes_viaje)]\n",
    "    if df_filtro.empty:\n",
    "        return 0\n",
    "        \n",
    "    precip_media = df_filtro['PRECIPITACION_TOTAL_MM'].mean()\n",
    "    \n",
    "    # Penalización algorítmica (Ej: >150mm es peligro extremo por huaicos)\n",
    "    if precip_media > 150:\n",
    "        score = 15  # Muy baja viabilidad\n",
    "    elif precip_media > 80:\n",
    "        score = 45\n",
    "    elif precip_media > 30:\n",
    "        score = 75\n",
    "    else:\n",
    "        score = 98  # Clima perfecto\n",
    "        \n",
    "    return score\n",
    "\n",
    "# Prueba de Predicción\n",
    "mes_solicitado = 2 # Febrero\n",
    "region_solicitada = 'CUSCO'\n",
    "score = calcular_score_viabilidad(region_solicitada, mes_solicitado)\n",
    "print(f\"Predicción de Viabilidad para {region_solicitada} en el mes {mes_solicitado}: {score}%\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Inyección de Comercio Local Dinámico (Recomendador B2B)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cargar ferias y eventos (El Flywheel de monetización)\n",
    "df_eventos = pd.read_csv('../data/comercios_ferias_locales.csv', sep=';')\n",
    "df_eventos['FECHA_INICIO'] = pd.to_datetime(df_eventos['FECHA_INICIO'])\n",
    "df_eventos['FECHA_FIN'] = pd.to_datetime(df_eventos['FECHA_FIN'])\n",
    "print(f\"Comercios locales registrados: {len(df_eventos)}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "def recomendar_eventos_locales(region, fecha_viaje_usuario):\n",
    "    \"\"\"\n",
    "    Simula el recomendador de inyección de anuncios/eventos en la ruta del usuario.\n",
    "    Filtra por cruce temporal y ordena por relevancia (CTR proxy).\n",
    "    \"\"\"\n",
    "    fecha = pd.to_datetime(fecha_viaje_usuario)\n",
    "    \n",
    "    # Condición de coincidencia espacio-temporal\n",
    "    eventos_activos = df_eventos[\n",
    "        (df_eventos['REGION'] == region) &\n",
    "        (df_eventos['FECHA_INICIO'] <= fecha) &\n",
    "        (df_eventos['FECHA_FIN'] >= fecha)\n",
    "    ].copy()\n",
    "    \n",
    "    # Ordenar por el peso de la publicidad para maximizar revenue\n",
    "    recomendaciones = eventos_activos.sort_values(by='RELEVANCIA_PUBLICIDAD', ascending=False).head(3)\n",
    "    return recomendaciones[['NOMBRE_EVENTO', 'CATEGORIA', 'COSTO_PEN', 'RELEVANCIA_PUBLICIDAD']]\n",
    "\n",
    "# Simulación: Turista viaja a Cusco el 15 de Noviembre de 2024\n",
    "eventos_recomendados = recomendar_eventos_locales('CUSCO', '2024-11-15')\n",
    "print(\"Eventos Comerciales Inyectados a la Ruta:\")\n",
    "eventos_recomendados"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

with open('/home/miguel/Escritorio/UTEC/2026-2/DPD/Proyecto/deliveries/week06/code/DreemGO_Predictive_Engine.ipynb', 'w') as f:
    json.dump(notebook_structure, f, indent=1)
