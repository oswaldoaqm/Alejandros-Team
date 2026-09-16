import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# DreemGO - Exploratory Data Analysis (EDA) & Análisis Predictivo\n",
    "--- \n",
    "Este notebook contiene el análisis de las tres fuentes de datos que alimentan el motor de DreemGO:\n",
    "1. **Inventario Espacial** (MINCETUR Enriquecido)\n",
    "2. **Series de Tiempo Climáticas** (Open-Meteo 10 años)\n",
    "3. **Eventos y Comercios Dinámicos** (Marketplace Turístico)"
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
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "sns.set_theme(style=\"whitegrid\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Análisis Espacial (Catálogo Turístico Estático)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Cargar Data Maestra y eliminar la columna de texto irrelevante (Feature Selection)\n",
    "df_master = pd.read_csv('../data/processed/dreemgo_master_dataset.csv', sep=';')\n",
    "if 'EPOCA_PROPICIA' in df_master.columns:\n",
    "    df_master = df_master.drop(columns=['EPOCA_PROPICIA']) # Eliminamos texto manual en favor del modelo predictivo\n",
    "\n",
    "# Limpieza rápida de coordenadas para el mapa\n",
    "df_master['latitud'] = pd.to_numeric(df_master['latitud'], errors='coerce')\n",
    "df_master['longitud'] = pd.to_numeric(df_master['longitud'], errors='coerce')\n",
    "df_mapa = df_master[(df_master['latitud'] < 0) & (df_master['longitud'] < -60)]\n",
    "\n",
    "plt.figure(figsize=(8, 10))\n",
    "sns.scatterplot(data=df_mapa, x='longitud', y='latitud', hue='JERARQUIA_OFICIAL', palette='viridis', s=15, alpha=0.8)\n",
    "plt.title('Densidad de Recursos Turísticos en Perú (Clasificados por Jerarquía)')\n",
    "plt.xlabel('Longitud')\n",
    "plt.ylabel('Latitud')\n",
    "plt.legend(title='Jerarquía Turística')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Análisis Climático (Forecasting Meteorológico a 10 Años)\n",
    "En lugar de depender de reglas de texto estáticas, el sistema analiza el comportamiento real de la precipitación para predecir la seguridad de la ruta."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "df_clima = pd.read_csv('../data/processed/historial_clima_regiones.csv', sep=';')\n",
    "df_clima['MES'] = df_clima['MES'].astype(int)\n",
    "\n",
    "# Comparativa de precipitaciones: Costa vs Sierra vs Selva\n",
    "regiones_muestra = ['PIURA', 'CUSCO', 'LORETO']\n",
    "df_muestra_clima = df_clima[df_clima['REGION'].isin(regiones_muestra)]\n",
    "\n",
    "plt.figure(figsize=(12, 6))\n",
    "sns.lineplot(data=df_muestra_clima, x='MES', y='PRECIPITACION_TOTAL_MM', hue='REGION', errorbar='sd')\n",
    "plt.title('Curva de Estacionalidad de Lluvias (Promedio 2014-2023)')\n",
    "plt.xticks(range(1, 13))\n",
    "plt.ylabel('Precipitación Total (mm)')\n",
    "plt.xlabel('Mes del Año')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Análisis de Monetización (Eventos Locales)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "df_comercio = pd.read_csv('../data/processed/comercios_ferias_locales.csv', sep=';')\n",
    "\n",
    "plt.figure(figsize=(10, 5))\n",
    "sns.countplot(data=df_comercio, y='CATEGORIA', order=df_comercio['CATEGORIA'].value_counts().index, palette='mako')\n",
    "plt.title('Distribución de Eventos Dinámicos por Categoría (Marketplace)')\n",
    "plt.xlabel('Cantidad de Eventos / Anuncios')\n",
    "plt.ylabel('Categoría')\n",
    "plt.show()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

with open('/home/miguel/Escritorio/UTEC/2026-2/DPD/Proyecto/deliveries/week06/code/DreemGO_Advanced_EDA.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)
