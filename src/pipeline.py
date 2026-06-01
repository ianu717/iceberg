"""
pipeline.py - Orquestador del ETL de Txoko.

Ejecuta las etapas en orden:
    EXTRACT   (descarga JSONs de Open Data Euskadi -> data/raw/)
    TRANSFORM (normaliza + limpia -> DataFrame maestro + CSV)
    LOAD      (vuelca a la BD con columna geográfica PostGIS)

Uso:
    uv run python -m src.pipeline                # pipeline completo
    uv run python -m src.pipeline --skip-extract # reutiliza raw/ ya descargado
    uv run python -m src.pipeline --no-load      # solo hasta el CSV maestro

IMPORTANTE: para que LOAD funcione contra PostgreSQL hay que tener
la extensión PostGIS activada en la base:  CREATE EXTENSION IF NOT EXISTS postgis;
"""

import argparse
import logging

from . import extract, transform, load

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("pipeline")


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL Txoko")
    parser.add_argument("--skip-extract", action="store_true",
                        help="No descargar; usar los JSON ya en data/raw/")
    parser.add_argument("--no-load", action="store_true",
                        help="No cargar a la BD; quedarse en el CSV maestro")
    parser.add_argument("--no-recrear", action="store_true",
                        help="No borrar/recrear las tablas antes de cargar")
    args = parser.parse_args()

    if not args.skip_extract:
        logger.info("== EXTRACT ==")
        extract.run()
    else:
        logger.info("== EXTRACT (saltado) ==")

    logger.info("== TRANSFORM ==")
    df = transform.run(guardar_csv=True)

    if not args.no_load:
        logger.info("== LOAD ==")
        load.run(df=df, recrear=not args.no_recrear)
    else:
        logger.info("== LOAD (saltado) ==")

    logger.info("Pipeline completado.")


if __name__ == "__main__":
    main()
