"""
load.py - LOAD.

Vuelca el DataFrame maestro a la base de datos (tabla 'lugares').
Convierte lat/lon en el punto geográfico PostGIS (columna ubicacion).

Estrategia: como en desarrollo el modelo aún cambia y la BD no tiene
datos valiosos, hacemos recreado completo (drop + create) por defecto.
Cuando el esquema se estabilice, migrar a Alembic.
"""

import logging

import pandas as pd

from .db import engine, SessionLocal, Base
from .models import Lugar

logger = logging.getLogger(__name__)


def _punto_wkt(lat, lon):
    """Devuelve el punto en formato WKT 'POINT(lon lat)' o None.
    OJO: en WKT el orden es lon primero, lat después."""
    if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
        return None
    return f"POINT({lon} {lat})"


def _valor(v):
    """Normaliza NaN/strings vacíos a None para la BD."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


def recrear_tablas():
    """Borra y recrea las tablas (solo para desarrollo)."""
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
                direccion=_valor(row.get("direccion")),
                telefono=_valor(row.get("telefono")),
                web=_valor(row.get("web")),
                ficha_turismo=_valor(row.get("ficha_turismo")),
            ))
            # Volcado por lotes para no acumular todo en memoria de la sesión.
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
        print(id)
        session.rollback()
        raise
    finally:
        session.close()
    return insertados


def run(df=None, recrear=True):
    """LOAD completo. Si no se pasa df, lee el CSV maestro de disco."""
    if df is None:
        from config import PROCESSED_DIR
        df = pd.read_csv(PROCESSED_DIR / "txoko_master.csv")
    return cargar(df, recrear=recrear)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()
