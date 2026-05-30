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
#  2) Se arranca vía shell para que $PORT se expanda.
#  3) DATABASE_URL la inyecta Render desde su PostgreSQL
#     gestionado (no se hardcodea aquí).
# ============================================================

# ---------- STAGE 1: builder ----------
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Instalar SOLO dependencias primero (capa cacheable).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copiar el código e instalarlo.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- STAGE 2: imagen final ----------
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Usuario no root (buena práctica de seguridad).
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Render asigna el puerto vía $PORT. EXPOSE es informativo;
# el valor real lo pone Render en runtime. Damos 8000 como
# fallback para ejecutar en local sin definir PORT.
ENV PORT=8000
EXPOSE 8000

# IMPORTANTE: forma "shell" para que ${PORT} se expanda.
CMD uvicorn api.api:app --host 0.0.0.0 --port ${PORT}