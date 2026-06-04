"""
db.py - Conexión a la base de datos con SQLAlchemy.

Lee DATABASE_URL del entorno (vía .env en local, variables de entorno
en Render). El mismo código sirve para el pipeline ETL y para la API.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carga el .env en local. En producción (Render) no hay .env y no hace
# nada; la variable ya está inyectada en el entorno.
load_dotenv()

DATABASE_URL = str(os.environ.get("DATABASE_URL"))

# Render entrega a veces "postgres://"; SQLAlchemy espera "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Dependencia FastAPI: una sesión por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
