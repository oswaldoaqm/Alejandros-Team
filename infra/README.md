# Infraestructura

El API corre como una función **AWS Lambda con imagen de contenedor**, detrás de una **HTTP API**, con una tabla **DynamoDB** para los eventos que publican los municipios. Está descrito en [`template.yaml`](./template.yaml) con AWS SAM. La app web es estática y se publica en **GitHub Pages**, fuera de AWS.

La decisión y sus alternativas están en [`../docs/decisiones/0002-stack-y-despliegue.md`](../docs/decisiones/0002-stack-y-despliegue.md).

## Antes de desplegar, una sola vez

1. Una cuenta de AWS, con autenticación de dos factores en el usuario raíz.
2. **Una alarma de presupuesto** en AWS Budgets, de USD 1. Es la protección contra una sorpresa en la tarjeta.
3. Un usuario o perfil con permisos para CloudFormation, Lambda, API Gateway, DynamoDB, ECR e IAM. No se usan las credenciales del usuario raíz.
4. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) y Docker instalados, y `aws configure` hecho.

Las credenciales nunca entran al repositorio: `.gitignore` excluye `.aws/`, `.env*`, `samconfig.toml` y las claves.

## Desplegar

Desde la raíz del repositorio:

```bash
cp infra/samconfig.example.toml infra/samconfig.toml
sam build --template-file infra/template.yaml --config-file samconfig.toml
sam deploy --config-file samconfig.toml --parameter-overrides \
  OrigenesCors=https://oswaldoaqm.github.io ClavePublicador=<una-clave-larga>
```

`sam deploy` crea el repositorio de imágenes, sube la imagen y deja la URL del API en la salida `UrlApi`. Esa URL es la que recibe la app en `VITE_API_URL`: se guarda en la variable `API_URL` del repositorio y la app publicada la toma en su siguiente build ([`app/README.md`](../app/README.md#publicarla)). Para comprobarlo:

```bash
curl https://<id>.execute-api.sa-east-1.amazonaws.com/v1/salud
```

La primera petición después de un rato sin uso tarda más: es el arranque en frío de Lambda. Se mide después del primer despliegue y se anota en el informe de la semana 10.

`ClavePublicador` es la clave con la que los municipios publican eventos. Se genera una larga, por ejemplo con `python -c "import secrets; print(secrets.token_urlsafe(32))"`, y se le da solo a quien publica: no entra al repositorio ni a un chat. Si se deja vacía, nadie publica.

## Los eventos publicados

`POST /v1/eventos` guarda cada evento en la tabla de DynamoDB; su nombre sale en la salida `TablaEventos` del despliegue. Quién puede publicar, qué se acepta y dónde aparece lo publicado está en [`docs/CONTRATO.md`](../docs/CONTRATO.md) §4.1, y el porqué en la [decisión 0011](../docs/decisiones/0011-eventos-publicados.md). La app tiene la misma función en «Para municipios: publicar un evento». Para probar el despliegue sin la app:

```bash
curl -X POST https://<id>.execute-api.sa-east-1.amazonaws.com/v1/eventos \
  -H "Content-Type: application/json" -H "X-Clave-Publicador: <la-clave>" \
  -d '{"nombre": "Festival de prueba", "fecha_inicio": "2026-11-13", "fecha_fin": "2026-11-15",
       "distrito": "Huaraz", "provincia": "Huaraz", "region": "Áncash",
       "lat": -9.5279, "lon": -77.5286, "publicado_por": "Equipo DreemGO (prueba)"}'
```

Responde 201 con el evento, y `/v1/salud` pasa a decir `version_datos: "2026.10.2-e…"`: la versión de los artefactos más la huella de lo publicado.

- **Corregir un evento:** se publica otra vez con el mismo nombre, fechas, lugar y entidad.
- **Retirarlo:** todavía no se puede por el API. A mano, con el `id` que devolvió al publicarlo:

  ```bash
  aws dynamodb delete-item --table-name <TablaEventos> --key '{"id": {"S": "p-…"}}'
  ```

  Deja de salir en las respuestas en un minuto: borrar a mano no les avisa a los servidores, que de todos modos vuelven a leer la tabla cada minuto.
- **Los que ya pasaron** los borra DynamoDB sola unos días después de su último día: el API le pone a cada evento cuándo expira.
- **Cambiar la clave:** se despliega otra vez con otro valor en `ClavePublicador`.
- **El ítem `#marca`** de la tabla no es un evento: cambia con cada publicación y es lo que cada servidor mira para enterarse de lo que publicó otro. No vence y no hay que borrarlo.

## Costo esperado

Con el tráfico del curso, cero o centavos. Lambda incluye 1 millón de peticiones y 400 000 GB-segundo al mes sin costo; la tabla usa capacidad provisionada de 5 lecturas y 1 escritura por segundo, muy por debajo de las 25 y 25 que DynamoDB incluye sin costo; la HTTP API está limitada a 10 peticiones por segundo para que un abuso no se convierta en factura. Las condiciones de la capa gratuita cambian: conviene mirarlas en la consola de facturación al crear la cuenta, y para eso está la alarma de USD 1. Lo único que puede costar algo es guardar imágenes viejas en ECR: se borran las que ya no se usan.

Mientras atiende pedidos, cada servidor despierto le pregunta a la tabla cada dos segundos si alguien publicó (una unidad de lectura cada vez), y la lee entera cuando la respuesta cambió y, de todos modos, una vez por minuto. Con el tope de 500 eventos por venir, y eventos como el del ejemplo, son unas 90 unidades de lectura por minuto y por servidor; la tabla da 300. Cada publicación son dos escrituras: el evento y la marca.

## Quitar todo

```bash
sam delete --stack-name dreemgo --region sa-east-1
```

Se lleva también la tabla, con los eventos publicados.

## Sin cuenta de AWS

La imagen es la misma en cualquier parte. Mientras no haya cuenta, o si algo falla, corre en local o en un host de contenedores:

```bash
docker build -f infra/Dockerfile -t dreemgo-api .
docker run -p 8080:8080 -e DREEMGO_CORS=http://localhost:5173 dreemgo-api
```

Así el API responde consultas pero no acepta publicaciones, porque no tiene clave. Para que las acepte y las guarde en un archivo que sobreviva a los reinicios, en un volumen:

```bash
docker run -p 8080:8080 -e DREEMGO_CORS=http://localhost:5173 \
  -e DREEMGO_CLAVE_PUBLICADOR=<una-clave-larga> \
  -e DREEMGO_EVENTOS_ARCHIVO=/datos/eventos.jsonl -v dreemgo-eventos:/datos \
  dreemgo-api
```

## Las variables que lee el API

| Variable | Qué hace | Si falta |
|---|---|---|
| `DREEMGO_CORS` | Orígenes que pueden llamar al API desde el navegador, separados por comas | La app publicada y `http://localhost:5173` |
| `DREEMGO_CLAVE_PUBLICADOR` | La clave que exige `POST /v1/eventos` | Nadie publica |
| `DREEMGO_TABLA_EVENTOS` | La tabla de DynamoDB donde se guardan los eventos publicados. La pone `template.yaml` | Se mira la variable siguiente |
| `DREEMGO_EVENTOS_ARCHIVO` | El archivo donde se guardan, una línea de JSON por evento. Lo pueden compartir varios procesos del API | Quedan en memoria y se pierden al reiniciar: sirve para desarrollar, con un solo proceso |
