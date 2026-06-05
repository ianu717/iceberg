"""
load.py - LOAD del dataset maestro (aupa_master_v5) a la BD.

Vuelca el CSV maestro a la tabla 'lugares', convirtiendo lat/lon en el
punto geográfico PostGIS y mapeando las columnas de Google, las señales
del modelo y las recomendaciones.

Ejecutar manualmente:
    uv run python -m src.load
    # o con un CSV concreto:
    uv run python -m src.load --csv data/processed/aupa_master_v5.csv

Estrategia: recreado completo (drop + create) por defecto en desarrollo.
Cuando el esquema se estabilice, migrar a Alembic.

IMPORTANTE: requiere PostGIS activado en la BD:
    CREATE EXTENSION IF NOT EXISTS postgis;
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.db.db import engine, SessionLocal, Base
from src.db.models import Lugar

logger = logging.getLogger(__name__)

# Ruta por defecto del CSV maestro. Ajusta si tu config usa otra.
DEFAULT_CSV = Path("data/processed/aupa_master_v7.csv")


def _punto_wkt(lat, lon):
    """Punto WKT 'POINT(lon lat)' o None. OJO: lon primero, lat después."""
    if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
        return None
    return f"POINT({lon} {lat})"


def _valor(v):
    """Normaliza NaN/strings vacíos a None."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


def _entero(v):
    """A int o None (los enteros con NaN llegan como float desde pandas)."""
    v = _valor(v)
    return int(v) if v is not None else None


def _booleano(v):
    """A bool o None. Acepta 0/1, True/False, 'true'/'false'."""
    v = _valor(v)
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(int(v))
    return str(v).strip().lower() in ("true", "1", "yes", "si", "sí")


def recrear_tablas():
    """Borra y recrea las tablas (solo desarrollo)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas recreadas")


def cargar(df, recrear=True, batch=500):
    """Inserta los registros del DataFrame maestro en la tabla lugares."""
    if recrear:
        recrear_tablas()

    session = SessionLocal()
    insertados = 0
    try:
        objetos = []
        for _, row in df.iterrows():
            lat, lon = _valor(row.get("lat")), _valor(row.get("lon"))
            objetos.append(Lugar(
                id=row["id"],
                source_dataset=_valor(row.get("source_dataset")),
                categoria=_valor(row.get("categoria")),
                subcategoria=_valor(row.get("subcategoria")),
                nombre=row["nombre"],
                descripcion=_valor(row.get("descripcion")),
                municipio=_valor(row.get("municipio")),
                territorio=_valor(row.get("territorio")),
                lat=lat,
                lon=lon,
                ubicacion=_punto_wkt(lat, lon),
                web=_valor(row.get("web")),
                ficha_turismo=_valor(row.get("ficha_turismo")),
                # Google
                google_place_id=_valor(row.get("google_place_id")),
                google_rating=_valor(row.get("google_rating")),
                google_num_reviews=_entero(row.get("google_num_reviews")),
                google_match_conf=_valor(row.get("google_match_conf")),
                # Señales del modelo
                local_ratio=_valor(row.get("local_ratio")),
                local_ratio_confidence=_valor(row.get("local_ratio_confidence")),
                signal_category=_valor(row.get("signal_category")),
                signal_hidden=_valor(row.get("signal_hidden")),
                signal_language_norm=_valor(row.get("signal_language_norm")),
                signal_municipality=_valor(row.get("signal_municipality")),
                # Flags
                mappable=_booleano(row.get("mappable")),
                has_google_data=_booleano(row.get("has_google_data")),
                excluir_modelo=_booleano(row.get("excluir_modelo")),
                # Recomendaciones por perfil
                rec_txoko_social=_booleano(row.get("rec_txoko_social")),
                rec_mendi_familia=_booleano(row.get("rec_mendi_familia")),
                rec_kultura=_booleano(row.get("rec_kultura")),
            ))
            if len(objetos) >= batch:
                session.bulk_save_objects(objetos)
                session.commit()
                insertados += len(objetos)
                objetos = []
        if objetos:
            session.bulk_save_objects(objetos)
            session.commit()
            insertados += len(objetos)
        logger.info("Cargados %d lugares en la BD", insertados)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return insertados


def run(df=None, recrear=True, csv_path=DEFAULT_CSV):
    """LOAD completo. Si no se pasa df, lee el CSV maestro de disco."""
    if df is None:
        logger.info("Leyendo CSV: %s", csv_path)
        df = pd.read_csv(csv_path)
        logger.info("Filas leídas: %d", len(df))
    return cargar(df, recrear=recrear)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Carga el CSV maestro a la BD")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Ruta al CSV maestro (aupa_master_v5.csv)")
    parser.add_argument("--no-recrear", action="store_true", help="No borrar/recrear las tablas antes de cargar")
    args = parser.parse_args()
    run(recrear=not args.no_recrear, csv_path=args.csv)