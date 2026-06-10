# 🧊 Aupa — Más allá del Guggen
 
> **Reto Inetum · Bootcamp BBK The Bridge · Equipo 4 Data · Desafío de Tripulaciones**  
> Aupa es una plataforma web/app para el País Vasco orientada a turistas que quieren descubrir lugares, establecimientos y actividades de forma auténtica. Desarrollada como respuesta al Reto Inetum dentro del Bootcamp BBK The Bridge.
 
---
 
## 🎯 Concepto
 
**Problema que resuelve**
 
Los turistas llegan al País Vasco y enfrentan 3 fricciones concretas:
 
No saben ubicarse — no conocen la ciudad, no saben qué hay cerca ni cómo moverse.
Buscan lo inmediato — su consulta real es "lo mejor cerca de mí ahora mismo".
Confían ciegamente en valoraciones — siguen Google Maps o TripAdvisor, que priorizan volumen de reseñas, no autenticidad local.
 
El resultado: todos van a los mismos sitios. El turista genuino queda frustrado.
 
**La hipótesis del iceberg**: los mejores sitios del País Vasco no son los más populares ni los más visibles. Están ocultos debajo de la superficie del turismo masivo — alta valoración, pocas reseñas. **Aupa** los encuentra.
 
La app asigna a cada lugar un **Local Score** (0–1) que mide su autenticidad local. Cuando el usuario hace el onboarding, el sistema lo clasifica en uno de **3 perfiles** y le muestra los lugares ordenados por relevancia para él.
 
---
 
## 👥 Equipo
 
| Rol | Nombre |
|---|---|
| Lead | Naia |
| Data | Andoni |
| API & Git Master | Unai |
| Data | Fátima |
 
---
 
## 📋 Tabla de contenidos
 
- [Arquitectura](#arquitectura)
- [Modelos ML](#modelos-ml)
  - [Modelo 1: Local Score](#modelo-1-local-score-gradientboosting)
  - [Modelo 2: Clustering de usuarios](#modelo-2-clustering-de-usuarios-kmeans)
- [Chatbot RAG](#chatbot-rag)
- [Stack tecnológico](#stack-tecnológico)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Instalación y desarrollo local](#instalación-y-desarrollo-local)
- [Ejecución con Docker](#ejecución-con-docker)
- [Variables de entorno](#variables-de-entorno)
- [Despliegue en Render](#despliegue-en-render)
- [API — Endpoints](#api--endpoints)
---
 
## Arquitectura
 
```
Usuario (onboarding)
        │  elige 3 prefs + duración + compañía
        ▼
  FastAPI (Uvicorn)
        │
        ├── /score  ──►  GradientBoosting  ──►  Local Score [0–1]
        │                (modelo_localscore.pkl)
        │
        ├── /profile ──► KMeans + StandardScaler ──► Perfil de usuario
        │                (modelo_clustering.pkl)      (Txoko Social /
        │                                              Mendi & Familia /
        │                                              Kultura)
        │
        ├── /chat   ──►  RAG Pipeline
        │                │
        │                ├── FAISS (índices vectoriales × 4 territorios)
        │                ├── paraphrase-multilingual-mpnet-base-v2
        │                └── Groq API (Llama 3.3 70B) ──► Respuesta natural
        │
        └── SQLAlchemy + GeoAlchemy2
                   │
                   └── PostgreSQL + PostGIS (Render)
                       Catálogo de lugares del País Vasco
```
 
---
 
## Modelos ML
 
### Modelo 1: Local Score (GradientBoosting)
 
Calcula cómo de "local" es un lugar en una escala 0–1.
 
**Features y su importancia:**
 
| Feature | Descripción | Importancia |
|---|---|---|
| `signal_category` | Tipo de lugar (sidrería, alojamiento, oficina…) | **43.5 %** |
| `signal_hidden` | Lugar sin presencia Google = joya oculta | **26.4 %** |
| `has_google_data` | ¿Tiene ficha Google? | ~15 % |
| `google_num_reviews` | Nº de reseñas (volumen) | ~10 % |
| `google_rating` | Puntuación Google | ~5 % |
| `signal_municipality` | Penalización por municipio turístico | 0.6 % |
| `signal_language_norm` | Idioma de las reseñas | 0.2 %* |
 
> \* Varianza casi nula en datos actuales: 97.1 % de las reseñas están en español. Mejorará en producción con más diversidad de datos.
 
**Rangos del Local Score:**
 
| Rango | Etiqueta |
|---|---|
| < 0.55 | 🔴 Turístico |
| 0.55 – 0.65 | 🟠 Mixto |
| 0.65 – 0.75 | 🔵 Local |
| > 0.75 | 🟢 Joya local |
 
**Métricas del modelo:**
 
- R² (CV 5-fold): validado con `KFold(n_splits=5, shuffle=True)`
- Algoritmo: `GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8)`
- Output: `model/modelo_localscore.pkl`, `model/resultados_modelo1.json`
---
 
### Modelo 2: Clustering de usuarios (KMeans)
 
Segmenta a cada usuario en un perfil de viaje basándose en su onboarding.
 
**Vector de usuario — 17 dimensiones:**
 
| Bloque | Dimensiones | Valores en producción |
|---|---|---|
| Preferencias | 15 | Binario: el usuario elige exactamente **3** de 15 |
| Duración (`duration`) | 1 | `oneday` / `threedays` / `oneweek` / `longstay` |
| Compañía (`companion`) | 1 | `solo` / `partner` / `friends` / `family` |
 
**Las 15 preferencias disponibles:**
`food`, `culture`, `nature`, `bars`, `local_favorites`, `shopping`, `coffee_shops`, `walking_tours`, `family_friendly`, `vegetarian_vegan`, `history`, `festivals_events`, `beaches`, `nightlife`, `budget_friendly`
 
**Resultado del clustering — K=3 (óptimo por codo + silhouette + Davies-Bouldin):**
 
| Cluster | Nombre | Arquetipos fusionados | Color |
|---|---|---|---|
| 0 | 🍻 **Txoko Social** | Gastronómico + Nocturno | `#D85A30` |
| 1 | 🏔️ **Mendi & Familia** | Naturaleza + Familiar | `#1A9E72` |
| 2 | 🎭 **Kultura** | Cultural (perfectamente separado) | `#7B5EA7` |
 
**Entrenamiento:** 1.000 usuarios sintéticos (5 arquetipos × 200, distribución Beta). El `StandardScaler` aprende sobre los sintéticos y aplica la misma transformación a los vectores reales de producción.
 
- Output: `model/modelo_clustering.pkl`, `model/scaler_clustering.pkl`, `model/resultados_modelo2.json`
---
 
## Chatbot RAG
 
Chatbot conversacional en lenguaje natural que permite consultas como:
 
> *"Recomiéndame un restaurante de pintxos cerca del Guggenheim"*  
> *"Playas tranquilas en Gipuzkoa"*  
> *"Algo auténtico y local en Bilbao, sin turistas"*  
> *"I want to visit a museum in San Sebastián"*
 
### ¿Qué es RAG?
 
**RAG = Retrieval-Augmented Generation.** El código busca en un índice vectorial los lugares más relevantes para la consulta y los inyecta como contexto en el prompt del LLM. El LLM no accede directamente a la base de datos — recibe texto y genera texto.
 
```
Consulta del usuario
        ↓
Detectar idioma (es / eu / en) + territorio + landmark + categoría
        ↓
Seleccionar índice FAISS correcto (bizkaia / gipuzkoa / araba / all)
        ↓
Búsqueda semántica → k=50 candidatos
        ↓
Filtros: categoría → proximidad al landmark → municipio
        ↓
Top 5 lugares + local_ratio → prompt
        ↓
Groq API (Llama 3.3 70B) → respuesta en lenguaje natural
```
 
### Stack del chatbot
 
| Componente | Tecnología |
|---|---|
| Embeddings | `paraphrase-multilingual-mpnet-base-v2` (768 dims) |
| Índice vectorial | FAISS `IndexFlatIP` × 4 (all, bizkaia, gipuzkoa, araba) |
| LLM | Groq + Llama 3.3 70B |
| Detección de idioma | `langdetect` |
| Landmarks | ~60 puntos de referencia con coordenadas GPS |
 
### Decisiones clave
 
- **4 índices territoriales separados:** FAISS solo entiende similitud semántica, no geografía. Con índices por territorio es imposible que "pintxos en Bilbao" devuelva resultados de Donostia.
- **Reseñas en el embedding (rating ≥ 3):** las reseñas reales responden mejor a consultas semánticas que las descripciones oficiales.
- **`local_ratio` en el prompt:** cuando el usuario pide "auténtico" o "sin turistas", el LLM prioriza lugares con puntuación ≥ 60/100.
- **Multilingüe:** un único espacio vectorial para español, euskera e inglés. La instrucción de idioma se inyecta dinámicamente con `langdetect` en cada consulta.
### Archivos del chatbot
 
```
backend/
├── main.py                  # Endpoint POST /chat
├── .env                     # GROQ_API_KEY (nunca al repo)
└── rag/
    ├── config.py            # Parámetros: FAISS_TOP_K=50, FINAL_TOP_K=5
    ├── index_loader.py      # Carga índices al arrancar (1 sola vez)
    ├── retrieval.py         # Pipeline de búsqueda con filtros
    ├── prompt.py            # Construcción del prompt
    ├── llm.py               # Llamada a Groq
    └── landmarks.py         # ~60 puntos de referencia
 
rag_assets/                  # Generados offline (build_faiss_index.py)
├── faiss_all.index
├── faiss_bizkaia.index
├── faiss_gipuzkoa.index
├── faiss_araba.index
└── faiss_metadata_*.json
```
 
> Para regenerar los índices ejecutar `build_faiss_index.py` y reiniciar el servidor manualmente (`--reload` no recarga ficheros `.index`).
 
---
 
## Stack tecnológico
 
| Capa | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Modelos ML | scikit-learn (GradientBoosting, KMeans, StandardScaler, PCA) |
| Chatbot | RAG · FAISS · sentence-transformers · Groq (Llama 3.3 70B) |
| Análisis | Pandas, NumPy, Seaborn, Sweetviz |
| Base de datos | PostgreSQL + PostGIS |
| ORM | SQLAlchemy + GeoAlchemy2 |
| Validación | Pydantic |
| Gestor de paquetes | [uv](https://docs.astral.sh/uv/) |
| Contenedor | Docker (multi-stage build) |
| Despliegue | [Render](https://render.com) |
| Python | 3.11+ |
 
---
 
## Estructura del repositorio
 
```
iceberg/
├── model/
│   ├── modelo_clustering.pkl       # KMeans serializado
│   └── resultados_modelo2.json     # Métricas del clustering
│
├── notebooks/
│   ├── aupa_analisis.ipynb                    # EDA + 4 hallazgos principales
│   ├── modelo_clustering.ipynb                # Entrenamiento KMeans
│   ├── modelo_localscore.ipynb                # Construcción del Local Score
│   ├── aupa_rag_chatbot_completo.ipynb        # Implementación completa del chatbot RAG
│   ├── MapeoNearby.ipynb                      # Mapeo de categorías
│   ├── txoko_pipeline_datos.ipynb             # Pipeline de datos maestro
│   ├── txoko_google_places.ipynb              # Enriquecimiento Google Places API
│   ├── txoko_google_reviews_enrich....ipynb   # Enriquecimiento reseñas Google
│   ├── txoko_enrichment_provenanc....ipynb    # Proveniencia del enriquecimiento
│   ├── txoko_master_enriched_v2.csv           # Dataset enriquecido intermedio
│   └── eda_txoko.html                         # Informe EDA (Sweetviz)
│
├── reports/                        # Figuras exportadas del clustering
│   ├── fig_distribucion_perfiles.png
│   ├── fig_elbow_silhouette.png
│   ├── fig_radar_clusters.png
│   └── fig_silhouette_analysis.png
│
├── src/
│   ├── api/
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── api_schemas.py          # Schemas Pydantic (request/response)
│   │   ├── service/
│   │   │   ├── __init__.py
│   │   │   └── recomendation_service.py  # Lógica de recomendación
│   │   ├── __init__.py
│   │   └── main.py                     # ← Entry point FastAPI
│   ├── db/
│   │   ├── __init__.py
│   │   ├── db.py                       # Conexión a PostgreSQL
│   │   └── models.py                   # Modelos SQLAlchemy
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   └── pipeline.py                 # Orquestador ETL
│   ├── inference/
│   │   ├── __init__.py
│   │   └── inference.py                # Carga modelos y ejecuta predicciones
│   ├── __init__.py
│   ├── config.py                       # Variables de configuración
│   └── utils.py
│
├── backend/                            # Chatbot RAG
│   ├── main.py                         # Endpoint POST /chat
│   ├── requirements.txt
│   └── rag/
│       ├── config.py
│       ├── index_loader.py
│       ├── retrieval.py
│       ├── prompt.py
│       ├── llm.py
│       └── landmarks.py
│
├── rag_assets/                         # Índices FAISS (generados offline)
│   ├── faiss_all.index
│   ├── faiss_bizkaia.index
│   ├── faiss_gipuzkoa.index
│   ├── faiss_araba.index
│   └── faiss_metadata_*.json
│
├── .dockerignore
├── .gitignore
├── .python-version                     # "3.11"
├── Dockerfile                          # Multi-stage con uv
├── README.md
├── entrypoint.sh                       # exec uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
├── pyproject.toml
└── uv.lock
```
 
---
 
## Instalación y desarrollo local
 
### 1. Clonar el repositorio
 
```bash
git clone https://github.com/ianu717/iceberg.git
cd iceberg
```
 
### 2. Instalar dependencias
 
```bash
uv sync
```
 
### 3. Configurar variables de entorno
 
Crea un archivo `.env` en la raíz (ver sección [Variables de entorno](#variables-de-entorno)).
 
### 4. Ejecutar la API
 
```bash
uv run uvicorn src.app.main:app --reload --port 8000
```
 
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
### 5. Ejecutar los notebooks
 
```bash
uv run jupyter lab
```
 
---
 
## Ejecución con Docker
 
```bash
# Build
docker build -t aupa-api .
 
# Run
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@host/dbname" \
  aupa-api
```
 
> El Dockerfile usa un **build multi-stage** (builder con `uv` + imagen final `python:3.11-slim`). El `entrypoint.sh` arranca Uvicorn respetando la variable `$PORT` de Render, con fallback a `8000` en local.
 
---
 
## Variables de entorno
 
| Variable | Descripción | Requerida |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL (`postgresql://...`) | ✅ |
| `GROQ_API_KEY` | API key de Groq para el chatbot | ✅ |
| `PORT` | Puerto de escucha (Render lo inyecta automáticamente) | ⚙️ Auto |
 
Ejemplo de `.env` para desarrollo local:
 
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/aupa_db
GROQ_API_KEY=tu_clave_aqui
```
 
> ⚠️ El `.env` está en `.gitignore`. Nunca lo subas al repositorio.
 
---
 
## Despliegue en Render
 
El proyecto se despliega en [Render](https://render.com) como **Web Service** a partir del `Dockerfile`.
 
Render gestiona automáticamente:
- Build de la imagen Docker en cada push a `main`
- Inyección de `$PORT` en runtime
- Base de datos PostgreSQL gestionada (la `DATABASE_URL` se configura en el panel de Render como variable de entorno)
---
 
## API — Endpoints
 
La documentación completa está disponible en `/docs` (Swagger UI) y `/redoc` con la API en marcha.
 
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado del servidor e índices cargados |
| POST | `/chat` | Consulta al chatbot RAG en lenguaje natural |
 
> **URL de producción:** `https://<tu-servicio>.onrender.com`
 
---
 
<div align="center">
  <sub>Hecho con 🧊 en Bilbao · Reto Inetum · BBK The Bridge · Equipo 4</sub>
</div>
