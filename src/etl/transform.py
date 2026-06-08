"""
transform.py - TRANSFORM.

Lee los JSON crudos de data/raw/, normaliza cada registro al esquema
maestro de Txoko, los apila (concat vertical), limpia y deduplica, y
devuelve el DataFrame maestro. También lo guarda como CSV maestro.
"""

import json
import re
import logging

import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR, CATEGORY_MAP

logger = logging.getLogger(__name__)


def _parse_coords(record):
    """Coordenadas: float o None si vacías."""
    try:
        lat = float(record.get("latwgs84") or 0) or None
        lon = float(record.get("lonwgs84") or 0) or None
    except (ValueError, TypeError):
        lat, lon = None, None
    return lat, lon


def _parse_address(record):
    """Dirección: puede ser string o dict anidado."""
    addr_raw = record.get("address", "")
    if isinstance(addr_raw, dict):
        return ", ".join(str(v) for v in addr_raw.values() if v and v not in ("", 0))
    return str(addr_raw) if addr_raw else ""


def _parse_municipio(record):
    """Municipio: normalizar espacios y capitalización."""
    municipio = (record.get("municipality") or record.get("locality") or "").strip()
    municipio = re.sub(r"\s+", " ", municipio)
    return municipio.title() if municipio.isupper() else municipio


def _parse_territorio(record):
    """Territorio: normalizar variantes y multi-territorio."""
    terr_raw = (record.get("territory") or "").strip().upper()
    terr_raw = re.sub(r"\s+", " ", terr_raw)
    terr_raw = (terr_raw.replace("ARABA/ÁLAVA", "ARABA")
                        .replace("ÁLAVA", "ARABA")
                        .replace("ALAVA", "ARABA"))

    matches = [t for t in ("ARABA", "BIZKAIA", "GIPUZKOA") if t in terr_raw]
    if len(matches) > 1:
        return "EUSKADI"
    return matches[0] if matches else "DESCONOCIDO"


def normalize_record(record, dataset_name):
    """Transforma UN registro JSON crudo al esquema maestro de Txoko."""
    cat, subcat = CATEGORY_MAP.get(dataset_name, ("Otros", dataset_name))
    lat, lon = _parse_coords(record)

    return {
        "source_dataset": dataset_name,
        "categoria": cat,
        "subcategoria": subcat,
        "nombre": record.get("documentName") or record.get("name") or "",
        "descripcion": (record.get("documentDescription") or ""),
        "municipio": _parse_municipio(record),
        "territorio": _parse_territorio(record),
        "lat": lat,
        "lon": lon,
        "direccion": _parse_address(record),
        "telefono": record.get("phone") or record.get("telephone") or "",
        "web": (record.get("web") or record.get("webpage") or
                record.get("physicalUrl") or record.get("friendlyUrl") or ""),
        "ficha_turismo": record.get("physicalUrl") or record.get("friendlyUrl") or "",
    }


def construir_maestro():
    """Lee todos los JSON de raw/, normaliza y apila en un DataFrame."""
    all_rows = []
    files = sorted(f for f in RAW_DIR.glob("*.json") if not f.name.startswith("_"))
    for fpath in files:
        name = fpath.stem
        data = json.loads(fpath.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = [data]
        rows = [normalize_record(r, name) for r in data]
        all_rows.extend(rows)
        logger.info("  + %-45s %4d registros", name, len(rows))
    df = pd.DataFrame(all_rows)
    logger.info("DataFrame sin limpiar: %d filas x %d columnas", len(df), len(df.columns))
    return df


def limpiar(df):
    """Filtra sin-nombre, deduplica y asigna ID único txk_NNNNN."""
    inicio = len(df)

    # 1) Quitar registros sin nombre.
    df = df[df["nombre"].str.strip().ne("")]
    logger.info("Filtro nombre vacío: %d -> %d", inicio, len(df))

    # 2) Deduplicar por (nombre normalizado, municipio, categoría).
    df["_n"] = df["nombre"].str.lower().str.strip().str.replace(r"\s+", " ", regex=True)
    antes = len(df)
    df = df.drop_duplicates(subset=["_n", "municipio", "categoria"], keep="first")
    df = df.drop(columns=["_n"])
    logger.info("Deduplicación: %d -> %d", antes, len(df))

    # 3) ID único txk_00001...
    df = df.reset_index(drop=True)
    df.insert(0, "id", [f"txk_{i+1:05d}" for i in range(len(df))])
    return df


def run(guardar_csv=True):
    """TRANSFORM completo: raw/ -> DataFrame maestro limpio (+ CSV opcional)."""
    df = construir_maestro()
    df = limpiar(df)
    if guardar_csv:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        out = PROCESSED_DIR / "iceberg.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        logger.info("Maestro guardado: %s (%d registros)", out, len(df))
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()
