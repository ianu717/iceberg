#!/bin/sh
# ============================================================
# Entrypoint para la API FastAPI (Render · Equipo 4)
# ------------------------------------------------------------
# - Render inyecta $PORT en runtime; aquí lo expandimos.
# - Usamos `exec` para que uvicorn REEMPLACE al shell y herede
#   el PID 1. Así uvicorn recibe SIGTERM/SIGINT directamente
#   del sistema operativo y el contenedor para de forma limpia.
# ============================================================
set -e

# Fallback a 8000 si PORT no viene definido (ejecución local).
: "${PORT:=8000}"

exec uvicorn api.api:app --host 0.0.0.0 --port "${PORT}"
