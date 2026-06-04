# 🧊 Iceberg — Más allá del Guggen

> **Equipo 4 · Desafío de Tripulaciones**  
> API REST geoespacial con análisis de datos y modelos predictivos, desplegada en Render.

---

## 📋 Tabla de contenidos

- [Descripción](#descripción)
- [Arquitectura del proyecto](#arquitectura-del-proyecto)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos previos](#requisitos-previos)
- [Instalación y desarrollo local](#instalación-y-desarrollo-local)
- [Ejecución con Docker](#ejecución-con-docker)
- [Variables de entorno](#variables-de-entorno)
- [Despliegue en Render](#despliegue-en-render)
- [API — Endpoints](#api--endpoints)
- [Notebooks y análisis](#notebooks-y-análisis)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Equipo](#equipo)

---

## Descripción

**Iceberg** es el backend del proyecto de análisis de datos del Equipo 4. Su nombre refleja la idea de que la mayor parte del valor de los datos se encuentra debajo de la superficie —más allá del icono más visible de Bilbao.

El proyecto expone una API REST construida con **FastAPI** que sirve datos geoespaciales almacenados en **PostgreSQL + PostGIS**, incluyendo modelos de machine learning entrenados con **scikit-learn** y análisis exploratorios generados con **Pandas**, **Seaborn** y **Sweetviz**.

---

## Arquitectura del proyecto

```
Cliente / Frontend
        │
        ▼
  FastAPI (Uvicorn)
        │
        ├── Rutas / Endpoints
        │       │
        │       ├── SQLAlchemy + GeoAlchemy2
        │       │         │
        │       │         └── PostgreSQL + PostGIS (Render)
        │       │
        │       └── Modelos ML (scikit-learn)
        │
        └── Pydantic (validación de datos)
```

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Base de datos | PostgreSQL + PostGIS (GeoAlchemy2) |
| ORM | SQLAlchemy |
| Machine Learning | scikit-learn, NumPy, Pandas |
| Visualización | Seaborn, Sweetviz |
| Validación | Pydantic |
| Gestor de paquetes | [uv](https://github.com/astral-sh/uv) |
| Contenerización | Docker (multi-stage build) |
| Despliegue | [Render](https://render.com) |
| Python | 3.11+ |

---

## Requisitos previos

- Python **3.11** o superior
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) instalado
- Docker (opcional, para ejecutar en contenedor)
- Una instancia de PostgreSQL con la extensión PostGIS habilitada

---

## Instalación y desarrollo local

### 1. Clonar el repositorio

```bash
git clone https://github.com/ianu717/iceberg.git
cd iceberg
```

### 2. Instalar dependencias con `uv`

```bash
uv sync
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto (ver sección [Variables de entorno](#variables-de-entorno)).

### 4. Ejecutar la API

```bash
uv run uvicorn src.app.main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`.  
La documentación interactiva (Swagger UI) en `http://localhost:8000/docs`.

---

## Ejecución con Docker

### Build de la imagen

```bash
docker build -t iceberg .
```

### Ejecutar el contenedor

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@host/dbname" \
  iceberg
```

> El Dockerfile usa un **build multi-stage** para mantener la imagen final ligera. El `entrypoint.sh` arranca Uvicorn respetando la variable `$PORT` inyectada por Render (fallback a `8000` en local).

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL (`postgresql://...`) | ✅ |
| `PORT` | Puerto en el que escucha la API (Render lo inyecta automáticamente) | ⚙️ Auto |

Ejemplo de `.env` para desarrollo local:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/iceberg_db
```

> ⚠️ **Nunca** commits el archivo `.env`. Está incluido en `.gitignore`.

---

## Despliegue en Render

El proyecto está configurado para desplegarse directamente en [Render](https://render.com) como un **Web Service** a partir del `Dockerfile`.

Render se encarga de:
- Construir la imagen Docker automáticamente en cada push a `main`
- Inyectar la variable `PORT` en runtime
- Proveer la base de datos PostgreSQL gestionada (la URL se configura como variable de entorno en el panel de Render)

Para redeploy manual, basta con hacer push a la rama `main`.

---

## API — Endpoints

La documentación completa y autogerada está disponible en `/docs` (Swagger UI) y `/redoc` una vez levantada la API.

> **URL de producción:** `https://<tu-servicio>.onrender.com`

---

## Notebooks y análisis

El directorio `notebooks/` contiene los análisis exploratorios (EDA) realizados durante el desarrollo del proyecto. Los informes generados se guardan en `reports/`.

Para ejecutar los notebooks:

```bash
uv run jupyter lab
```

---

## Estructura del repositorio

```
iceberg/
├── model/              # Modelos ML serializados
├── notebooks/          # Jupyter Notebooks (EDA y análisis)
├── reports/            # Informes y visualizaciones exportadas
├── src/
│   └── app/
│       └── main.py     # Punto de entrada de la aplicación FastAPI
├── .dockerignore
├── .gitignore
├── .python-version     # Python 3.11
├── Dockerfile          # Build multi-stage con uv
├── entrypoint.sh       # Script de arranque para Render/Docker
├── pyproject.toml      # Configuración del proyecto y dependencias
└── uv.lock             # Dependencias bloqueadas (no editar manualmente)
```

---

## Equipo

**Equipo 4 — "Más allá del Guggen"**

Proyecto desarrollado como parte de un Desafío de análisis de datos y desarrollo de APIs.

---

<div align="center">
  <sub>Hecho con 🧊 en Bilbao</sub>
</div>
