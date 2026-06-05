# syntax=docker/dockerfile:1.9
# ============================================================
# Dockerfile para RENDER  ·  Equipo 4 "Más allá del Guggen"
# API FastAPI gestionada con uv (build multi-stage).
# ------------------------------------------------------------
# Particularidades de Render que este Dockerfile respeta:
#  1) Render inyecta la variable de entorno PORT en runtime.
#     La app DEBE escuchar en $PORT y en 0.0.0.0, no en un
#     puerto fijo, o Render no detecta el servicio ("no open
#     ports detected").
#  2) El arranque se hace vía entrypoint.sh, que expande $PORT
#     y usa `exec` para que uvicorn sea PID 1 y reciba señales.
#  3) DATABASE_URL la inyecta Render desde su PostgreSQL
#     gestionado (no se hardcodea aquí).
# ============================================================

# ---------- STAGE 1: builder ----------
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Dependencias de compilación para psycopg2 (compilado desde fuente):
#  - build-essential: gcc, make y libc6-dev (cabeceras de C como stdlib.h)
#  - libpq-dev: cabeceras de PostgreSQL + pg_config
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar SOLO dependencias primero (capa cacheable).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# ------------------------------------------------------------
# Copias SELECTIVAS en lugar de `COPY . /app`.
# Copiamos únicamente lo estrictamente necesario para construir
# e instalar el proyecto. Así, aunque el .dockerignore se
# modifique por accidente, ficheros sensibles (.env, .git,
# credenciales, notebooks, datos, etc.) NUNCA entran en la imagen
# porque no están listados aquí.
#
# >>> PLANTILLA: ajusta estas líneas a la estructura real <<<
#     Añade un COPY por cada directorio/fichero de código que
#     tu aplicación necesite. NO uses `COPY . /app`.
# ------------------------------------------------------------
COPY pyproject.toml uv.lock entrypoint.sh .python-version ./
COPY src/ ./src/
COPY model/modelo_clustering.pkl ./model/
# COPY <otro_paquete>/ ./<otro_paquete>/
# COPY <otro_fichero_necesario> ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- STAGE 2: imagen final ----------
FROM python:3.11-slim-bookworm

# Librería de runtime de PostgreSQL (libpq) necesaria porque
# psycopg2 enlaza dinámicamente contra ella. NO instalamos la
# versión -dev aquí: solo la librería compartida de runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Copiar el entrypoint y darle permisos de ejecución.
COPY entrypoint.sh /app/entrypoint.sh

# Dar permisos de ejecución al entrypoint y crear el usuario no root
# en una sola instrucción RUN (buena práctica de seguridad y se
# reduce el número de capas de la imagen).
RUN chmod +x /app/entrypoint.sh \
    && useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# Render asigna el puerto vía $PORT. EXPOSE es informativo;
# el valor real lo pone Render en runtime. Damos 8000 como
# fallback para ejecutar en local sin definir PORT.
ENV PORT=8000
EXPOSE 8000

# Exec form: el entrypoint se ejecuta como PID 1 y, mediante
# `exec`, cede ese PID a uvicorn para que reciba las señales
# del SO y el contenedor pare limpiamente.
ENTRYPOINT ["/app/entrypoint.sh"]