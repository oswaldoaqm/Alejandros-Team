# Imagen del API de DreemGO.
#
# La misma imagen corre en local, en cualquier host de contenedores y en AWS Lambda.
# Lambda Web Adapter traduce los eventos de Lambda a peticiones HTTP hacia uvicorn;
# fuera de Lambda no hace nada. Se construye desde la raíz del repositorio:
#
#   docker build -f infra/Dockerfile -t dreemgo-api .
#   docker run -p 8080:8080 dreemgo-api        # http://localhost:8080/v1/docs

FROM public.ecr.aws/docker/library/python:3.12-slim

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.0.1 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/v1/salud

WORKDIR /app
COPY pyproject.toml README.md ./
COPY dreemgo ./dreemgo
RUN pip install ".[api]" && useradd --create-home --uid 1000 dreemgo
USER dreemgo

EXPOSE 8080
CMD ["uvicorn", "dreemgo.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
