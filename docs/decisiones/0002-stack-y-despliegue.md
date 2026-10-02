# 0002 · FastAPI en Lambda con imagen de contenedor; app estática en GitHub Pages

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente

## Contexto

La semana 10 pide un prototipo desplegado «cuando sea técnica y legalmente posible». El equipo sabe Python, el motor usa numpy ~~y OR-Tools~~ (ver la actualización), y no hay presupuesto. Todavía no hay cuenta de AWS.

## Decisión

- **Motor y API**: paquete `dreemgo` con FastAPI, empaquetado en una imagen de contenedor.
- **Despliegue**: la imagen corre en AWS Lambda con [Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter), detrás de una HTTP API, descrito con AWS SAM en `infra/template.yaml`. Región `sa-east-1` (São Paulo), la más cercana al Perú.
- **Eventos publicados**: una tabla DynamoDB con capacidad provisionada dentro de la capa gratuita.
- **App**: React, Vite y TypeScript, con mapa MapLibre; estática en GitHub Pages.
- **CI**: GitHub Actions corre lint, pruebas y construye y arranca la imagen en cada PR.

## Alternativas descartadas

- **Seis funciones Lambda y tres API Gateway** (arquitectura de la Delivery 1): seis despliegues y seis arranques en frío para un solo motor.
- **Mangum dentro de la imagen de Lambda**: ata la imagen a Lambda; con Web Adapter la misma imagen corre en local o en cualquier host.
- **Amplify**: GitHub Pages es gratuito y vive en el mismo repositorio.

## Consecuencias

- Mientras no haya cuenta de AWS, la imagen corre en local o en un host de contenedores gratuito; el cambio a Lambda es `sam deploy`.
- El arranque en frío se mide en el primer despliegue. Si pasa de 5 s, el plan B es cargar artefactos más livianos o precalentar antes de cada demo.
- La HTTP API limita a 10 peticiones por segundo para que un abuso no genere costo.

## Actualización · 2 de octubre de 2026

- **El motor no usa OR-Tools.** El itinerario lo arma un planificador propio sobre numpy ([0009](./0009-viaje-en-estrella.md)), y la imagen no lo lleva.
- **El host gratuito ya tiene receta:** un Space de Hugging Face, con [`infra/huggingface/Dockerfile`](../../infra/huggingface/Dockerfile). Corre el mismo paquete en 2 CPU y 16 GB; a cambio, lo que publican los municipios no dura y el Space se duerme tras 48 horas sin uso ([`infra/README.md`](../../infra/README.md)). Pasar a Lambda sigue siendo `sam deploy` y cambiar una variable de la app.
