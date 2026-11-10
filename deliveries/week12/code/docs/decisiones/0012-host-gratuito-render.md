# 0012 · El host gratuito pasa de un Space de Hugging Face a Render

**Fecha:** 5 de octubre de 2026 · **Estado:** vigente

## Contexto

La [actualización de la decisión 0002](./0002-stack-y-despliegue.md#actualización--2-de-octubre-de-2026) dejó
escrito que, mientras no hubiera cuenta de AWS, la imagen del API correría gratis en un Space de
**Hugging Face** con SDK Docker. Al intentar desplegarlo, la plataforma ya no lo permitía.

Hugging Face pasó los Spaces que consumen cómputo a plan de pago. Su
[documentación](https://huggingface.co/docs/hub/spaces-overview) lo dice hoy así:

> *"Static Spaces are free for everyone. Gradio and Docker Spaces run on compute and require a paid plan
> to create: PRO for personal accounts, Team or Enterprise for organizations."*

La única excepción para cuentas gratuitas son hasta **2 Spaces de Gradio con ZeroGPU**, que no sirven para
este caso: el API es un paquete FastAPI, no una aplicación Gradio. La opción quedó inservible sin cambiar
de tecnología, y la nota de 0002 era correcta cuando se escribió y dejó de serlo después.

## Decisión

- **El host gratuito de referencia pasa a ser [Render](https://render.com/).** Da 750 horas al mes de
  servicio web en su plan *Free*, sin pedir tarjeta, y construye la imagen desde el `Dockerfile` del
  repositorio con cada push a `main`.
- **La decisión principal no cambia:** AWS Lambda con imagen de contenedor sigue siendo el destino para
  cuando haya cuenta, porque es el único que conserva lo que publican los municipios y el que describe
  [`infra/template.yaml`](../../infra/template.yaml).
- **La imagen se vuelve portable de verdad.** [`infra/Dockerfile`](../../infra/Dockerfile) ahora toma el puerto de
  `PORT` y deja a uvicorn como proceso principal del contenedor, así que la misma imagen corre en Lambda
  (puerto 8080, el que pone la plantilla), en Docker local y en un host que inyecte su propio puerto, como
  Google Cloud Run, sin recompilarla.

## Alternativas descartadas

- **Pagar Hugging Face PRO**: resuelve el despliegue y contradice la restricción de no gastar. Si algún día
  se paga, [`infra/huggingface/Dockerfile`](../../infra/huggingface/Dockerfile) sigue sirviendo tal cual.
- **Google Cloud Run**: su capa gratuita es más generosa (2 millones de peticiones al mes) y no se duerme,
  pero exige cuenta de Google Cloud. Queda como la siguiente opción si Render deja de alcanzar.
- **Koyeb**: mantiene una instancia gratuita que no se duerme, con menos memoria. Queda como respaldo.
- **Una computadora del equipo expuesta con un túnel**: no da una dirección estable y deja el producto
  dependiendo de que alguien no apague su laptop.
- **Railway y Fly.io**: ya no tienen capa gratuita real, solo créditos de prueba.

## Consecuencias

- **Lo publicado sigue sin durar** fuera de AWS: vive en un archivo dentro del contenedor, así que se
  pierde con cada reinicio o redespliegue. Vale para la demostración; para que dure, la tabla de DynamoDB.
- **El host gratuito se duerme a los 15 minutos sin uso** (antes eran 48 horas), y la primera visita
  después tarda unos 50 segundos. Antes de una demostración hay que abrir `/v1/salud`.
- **El consumo entra de sobra**: el motor carga sus artefactos una sola vez y una consulta completa llega
  a **91 MB de pico**, contra los 512 MB del plan gratuito.
- **Si Render empieza a pedir tarjeta**, la receta se muda a Cloud Run o Koyeb sin tocar el código, porque
  la imagen ya respeta `PORT`.
