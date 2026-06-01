"""
models.py - Modelos de datos (SQLAlchemy ORM) para Txoko.

El modelo Lugar representa un punto de interés del dataset maestro.
Incluye una columna geográfica PostGIS (ubicacion) para las consultas
"cerca de mí". Se conserva también lat/lon como floats por comodidad
(para devolver al front sin tener que desempaquetar el punto).
"""

from sqlalchemy import Column, Integer, String, Float, Text, Index
from geoalchemy2 import Geography

from .db import Base


class Lugar(Base):
    __tablename__ = "lugares"

    # id propio de Txoko (txk_00001...). Lo usamos como clave primaria
    # porque ya es único y trazable desde el pipeline.
    id = Column(String(12), primary_key=True)

    # Procedencia (trazabilidad de la fuente).
    source_dataset = Column(String(80))

    # Clasificación.
    categoria = Column(String(40), index=True)
    subcategoria = Column(String(200))

    # Contenido.
    nombre = Column(String(300), nullable=False, index=True)
    descripcion = Column(Text)

    # Ubicación administrativa.
    municipio = Column(String(2000), index=True)
    territorio = Column(String(20), index=True)

    # Coordenadas en bruto (pueden ser NULL si el registro no tenía coords).
    lat = Column(Float)
    lon = Column(Float)

    # Punto geográfico PostGIS (SRID 4326 = GPS estándar). NULL si sin coords.
    # spatial_index=False aquí porque creamos el índice GiST aparte abajo.
    ubicacion = Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )

    # Contacto.
    direccion = Column(Text)
    telefono = Column(String(60))
    web = Column(String(400))
    ficha_turismo = Column(String(400))


# Índice espacial GiST sobre la columna geográfica -> acelera las
# búsquedas por cercanía (ST_DWithin / ST_Distance).
Index(
    "idx_lugares_ubicacion",
    Lugar.ubicacion,
    postgresql_using="gist",
)
