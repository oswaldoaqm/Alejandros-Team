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

`sam deploy` crea el repositorio de imágenes, sube la imagen y deja la URL del API en la salida `UrlApi`. Esa URL es la que recibe la app en `VITE_API_URL`. Para comprobarlo:

```bash
curl https://<id>.execute-api.sa-east-1.amazonaws.com/v1/salud
```

La primera petición después de un rato sin uso tarda más: es el arranque en frío de Lambda. Se mide después del primer despliegue y se anota en el informe de la semana 10.

## Costo esperado

Con el tráfico del curso, cero o centavos. Lambda incluye 1 millón de peticiones y 400 000 GB-segundo al mes sin costo; la tabla usa capacidad provisionada de 2 lecturas y 1 escritura, dentro de lo gratuito; la HTTP API está limitada a 10 peticiones por segundo para que un abuso no se convierta en factura. Lo único que puede costar algo es guardar imágenes viejas en ECR: se borran las que ya no se usan.

## Quitar todo

```bash
sam delete --stack-name dreemgo --region sa-east-1
```

## Sin cuenta de AWS

La imagen es la misma en cualquier parte. Mientras no haya cuenta, o si algo falla, corre en local o en un host de contenedores:

```bash
docker build -f infra/Dockerfile -t dreemgo-api .
docker run -p 8080:8080 -e DREEMGO_CORS=http://localhost:5173 dreemgo-api
```

Fuera de Lambda los eventos publicados se guardan en un archivo local en vez de DynamoDB.
