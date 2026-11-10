# El API de DreemGO en un Space de Hugging Face (infra/README.md, «Sin cuenta de AWS»).
#
# El Space solo necesita este archivo: el código se instala desde el repositorio público, en
# la versión que diga VERSION. Para publicar otra, se cambia esa línea por el commit de main
# que se quiere y el Space se reconstruye solo.

FROM python:3.12-slim

ARG VERSION=main

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DREEMGO_EVENTOS_ARCHIVO=/tmp/dreemgo/eventos.jsonl

# Los Spaces corren el contenedor con el usuario 1000.
RUN pip install "dreemgo[api] @ https://github.com/oswaldoaqm/Alejandros-Team/archive/${VERSION}.tar.gz" \
    && useradd --create-home --uid 1000 dreemgo
USER dreemgo
WORKDIR /home/dreemgo

# 7860 es el puerto que un Space espera. Dos procesos, uno por CPU: comparten lo publicado
# por el archivo de arriba, que dura lo que dure el contenedor.
EXPOSE 7860
CMD ["uvicorn", "dreemgo.api.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "2"]
