# 0001 · Sin cuentas: el viaje se comparte por enlace

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente

## Contexto

El diseño de la Delivery 1 tenía usuarios con contraseña (`USUARIO` en el modelo entidad-relación, Cognito en la arquitectura) para guardar preferencias y listar viajes. Eso obliga a proteger contraseñas y correos, cumplir la Ley 29733 de protección de datos personales y construir registro, ingreso y recuperación de cuenta, en seis semanas, para un producto cuyo valor está en el motor.

## Decisión

No hay cuentas. La consulta completa viaja en la URL y el motor es determinista, así que el enlace **es** el viaje guardado: quien lo abre ve lo mismo mientras no cambie la versión de datos, que también va en el enlace. Las preferencias del viajero se quedan en su navegador.

## Alternativas descartadas

- **Cuentas con Cognito**: costo de construcción y de cumplimiento alto; no mejora ninguna métrica del producto.
- **Guardar itinerarios con un identificador corto**: exige base de datos y política de retención para algo que el enlace ya resuelve.

## Consecuencias

- `GET /v1/viajes` recibe la consulta en la URL, igual que la app, y es cacheable.
- Publicar eventos sí necesita control: `POST /v1/eventos` exige una clave de publicador (cabecera `X-Clave-Publicador`), sin cuentas de viajero.
- «Mis viajes» queda en el almacenamiento local del navegador.
