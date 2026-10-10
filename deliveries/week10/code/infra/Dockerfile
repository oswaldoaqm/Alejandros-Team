# Imagen del API de DreemGO.
#
# La misma imagen corre en local, en cualquier host de contenedores y en AWS Lambda.
# Lambda Web Adapter traduce los eventos de Lambda a peticiones HTTP hacia uvicorn;
# fuera de Lambda no hace nada. Se construye desde la raíz del repositorio:
#
#   docker build -f infra/Dockerfile -t dreemgo-api .
#   docker run -p 8080:8080 dreemgo-api        # http://localhost:8080/v1/docs
#
# El puerto sale de PORT, que por defecto es 8080. Ese es el puerto que esperan AWS Lambda
# (lo pone template.yaml), Docker en local y hostes como Render. Google Cloud Run, en cambio,
# inyecta su propio PORT: con `docker run -e PORT=...`, el contenedor lo respeta sin cambios.

FROM public.ecr.aws/docker/library/python:3.12-slim

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.0.1 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/v1/salud

# Se puede cambiar en el build (`--build-arg PORT=…`) o al correr (`-e PORT=…`).
ARG PORT=8080

WORKDIR /app
COPY pyproject.toml README.md ./
COPY dreemgo ./dreemgo
# «aws» trae boto3, para la tabla de eventos publicados; fuera de AWS no se usa.
# /datos es donde va un volumen si los eventos se guardan en un archivo (infra/README.md).
RUN pip install ".[api,aws]" \
    && useradd --create-home --uid 1000 dreemgo \
    && mkdir /datos && chown dreemgo:dreemgo /datos
USER dreemgo

EXPOSE ${PORT}
# `exec` deja a uvicorn como proceso principal del contenedor: recibe bien la señal de apagado
# y `$PORT` se expande en tiempo de ejecución, así que `-e PORT=…` funciona sin recompilar.
CMD ["sh", "-c", "exec uvicorn dreemgo.api.app:app --host 0.0.0.0 --port ${PORT}"]
