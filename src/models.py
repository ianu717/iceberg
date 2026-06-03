"""
models.py - Modelos de datos (SQLAlchemy ORM) para Txoko/Aupa.

El modelo Lugar representa un punto de interés del dataset maestro
(aupa_master_v5). Incluye:
  - datos base (nombre, categoría, ubicación administrativa)
  - columna geográfica PostGIS (ubicacion) para "cerca de mí"
  - datos de Google (place_id, rating, num_reviews)
  - señales del modelo de ML (signal_*, local_ratio...)
  - flags y recomendaciones por perfil (rec_*)
"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Index
from geoalchemy2 import Geography

from .db import Base


class Lugar(Base):
    __tablename__ = "lugares"

    # id propio (txk_00000...). Clave primaria, único y trazable.
    id = Column(String(12), primary_key=True)

    # Procedencia.
    source_dataset = Column(String(80))

    # Clasificación.
    categoria = Column(String(40), index=True)
    subcategoria = Column(String(200))

    # Contenido.
    nombre = Column(String(300), nullable=False, index=True)
    descripcion = Column(Text)

    # Ubicación administrativa.
    # municipio amplio: algunos registros traen listas largas de municipios.
    municipio = Column(String(2000), index=True)
    territorio = Column(String(20), index=True)

    # Coordenadas en bruto (NULL si el registro no tenía coords).
    lat = Column(Float)
    lon = Column(Float)

    # Punto geográfico PostGIS (SRID 4326). NULL si sin coords.
    ubicacion = Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )

    # Enlaces.
    web = Column(String(400))
    ficha_turismo = Column(String(400))

    # --- Datos de Google Places ---
    # place_id puede superar el formato estándar en algunos registros.
    google_place_id = Column(String(200), index=True)
    google_rating = Column(Float)
    google_num_reviews = Column(Integer)
    google_match_conf = Column(String(20))      # 'high' / 'medium' / NULL

    # --- Señales del modelo y score de "localness" ---
    local_ratio = Column(Float)                 # ratio local (target/score)
    local_ratio_confidence = Column(String(20)) # 'high' / 'medium'
    signal_category = Column(Float)
    signal_hidden = Column(Float)
    signal_language_norm = Column(Float)
    signal_municipality = Column(Float)

    # --- Flags ---
    mappable = Column(Boolean)                   # tiene coords mapeables
    has_google_data = Column(Boolean)            # tiene datos de Google
    excluir_modelo = Column(Boolean)             # excluido del modelo

    # --- Recomendaciones por perfil (etiquetas 0/1) ---
    rec_txoko_social = Column(Boolean)
    rec_mendi_familia = Column(Boolean)
    rec_kultura = Column(Boolean)


# Índice espacial GiST -> acelera ST_DWithin / ST_Distance.
Index(
    "idx_lugares_ubicacion",
    Lugar.ubicacion,
    postgresql_using="gist",
)