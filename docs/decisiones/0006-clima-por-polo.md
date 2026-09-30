# 0006 · Clima diario en el centro de cada polo, no en la capital regional

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente

## Contexto

La estacionalidad de la semana 6 usaba un punto de clima por región, en su capital. El polo de Pozuzo, a 748 m en selva alta, recibía el clima de Cerro de Pasco, a más de 4 000 m. Agrupar por región y zona climática tampoco alcanza: 73 de esos 88 grupos pasan de 60 km de radio. Ningún polo pasa de 80 km de diámetro.

## Decisión

Un punto por polo, en su centro: clima diario 2016-2025 de Open-Meteo (reanálisis ERA5 y ERA5-Land), con lluvia, horas de lluvia, nieve, horas de sol y temperaturas. La temperatura se lleva a la altitud del punto base con el gradiente estándar; no se pide a la altitud mediana del polo porque en polos con nevados esa mediana es la de las cumbres.

## Alternativas descartadas

- **88 puntos región × zona climática** (`fetch_climate_v2.py`): grupos demasiado extensos.
- **Un punto por recurso**: 4 915 puntos a 261 llamadas cada uno no caben en la cuota gratuita en meses.

## Consecuencias

- La cuota gratuita de Open-Meteo (10 000 llamadas al día, 600 por minuto) alcanza para 36 polos por día: seis días para los 222, empezando por los más recomendados.
- Las horas de sol permiten distinguir el invierno gris de la costa, que casi no registra lluvia.
