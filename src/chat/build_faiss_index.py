"""
build_faiss_index.py
====================
Genera embeddings de los lugares turísticos y construye el índice FAISS.

Inputs:
    - aupa_master_v7.csv         → datos principales de cada lugar
    - txoko_reviews_raw.json     → reseñas de Google (hasta 5 por lugar)

Outputs:
    - faiss_index.index          → índice FAISS (búsqueda vectorial)
    - faiss_metadata.json        → metadatos de cada lugar (mismo orden que el índice)

Uso:
    python build_faiss_index.py \
        --csv aupa_master_v7.csv \
        --reviews txoko_reviews_raw.json \
        --output-dir .

El índice solo se regenera cuando cambian los datos fuente.
En producción, ejecutar este script offline y subir los dos archivos de output.
"""

import argparse
import json
import os
import time

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ─── Configuración ────────────────────────────────────────────────────────────

# Modelo multilingüe, buen equilibrio calidad/velocidad, corre sin GPU
# Alternativa más potente (más lenta): "paraphrase-multilingual-mpnet-base-v2"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Columnas del CSV que se usan para construir el texto de cada lugar
# Orden importa: lo que va primero tiene más peso semántico
CSV_TEXT_COLS = ["nombre", "subcategoria", "categoria", "descripcion", "municipio", "territorio"]

# Número máximo de reseñas por lugar que se incorporan al texto
MAX_REVIEWS = 5


# ─── Funciones ────────────────────────────────────────────────────────────────

def build_place_text(row: pd.Series, reviews_by_id: dict) -> str:
    """
    Construye el texto que se convertirá en embedding para un lugar.

    Combina los campos estructurados del CSV con las reseñas de Google.
    Las reseñas añaden vocabulario natural que mejora la búsqueda semántica:
    la descripción oficial dice "cocina vasca tradicional", una reseña dice
    "las croquetas son increíbles, perfecto para una cena tranquila".

    Formato final:
        Nombre: ELKANO
        Tipo: Restaurante / Asadores | Culinario
        Ubicación: Getaria, GIPUZKOA
        Descripción: ...
        Reseñas: Una experiencia increíble... | El mejor pescado...
    """
    parts = []

    # Campos estructurados
    parts.append(f"Nombre: {row.get('nombre', '')}")
    parts.append(f"Tipo: {row.get('subcategoria', '')} | {row.get('categoria', '')}")
    parts.append(f"Ubicación: {row.get('municipio', '')}, {row.get('territorio', '')}")

    desc = str(row.get("descripcion", "")).strip()
    if desc and desc != "nan":
        parts.append(f"Descripción: {desc}")

    # Reseñas (si existen para este lugar)
    place_id = str(row.get("id", ""))
    if place_id in reviews_by_id:
        reviews = reviews_by_id[place_id]
        # Solo reseñas con texto y con rating >= 3 para evitar ruido de reseñas negativas
        # que podrían asociar vocabulario negativo al lugar
        texts = [
            r["text"].strip()
            for r in reviews[:MAX_REVIEWS]
            if r.get("text", "").strip() and r.get("rating", 0) >= 3
        ]
        if texts:
            parts.append("Reseñas: " + " | ".join(texts))

    return "\n".join(parts)


def load_reviews(reviews_path: str) -> dict:
    """
    Carga el JSON de reseñas y lo transforma en un dict plano:
        {id_lugar: [{"rating": 5, "text": "..."}, ...]}

    El JSON puede tener dos estructuras según cómo se generó:
        - {id: {reviews: [...]}}           ← formato txoko_reviews_raw.json
        - {id: {place_id, rating, reviews}} ← mismo formato con más campos
    """
    with open(reviews_path, encoding="utf-8") as f:
        raw = json.load(f)

    reviews_by_id = {}
    for place_id, data in raw.items():
        if isinstance(data, dict) and "reviews" in data:
            reviews_by_id[place_id] = data["reviews"]
        elif isinstance(data, list):
            # Si ya es lista directamente
            reviews_by_id[place_id] = data

    print(f"  Reseñas cargadas: {len(reviews_by_id)} lugares con reseñas")
    return reviews_by_id


def build_metadata(row: pd.Series) -> dict:
    """
    Extrae los metadatos que se guardan junto al índice.
    Estos son los datos que el backend devuelve al frontend cuando
    recupera un lugar: no se vuelve a consultar la BD para esto.
    """
    return {
        "id":               str(row.get("id", "")),
        "nombre":           str(row.get("nombre", "")),
        "categoria":        str(row.get("categoria", "")),
        "subcategoria":     str(row.get("subcategoria", "")),
        "municipio":        str(row.get("municipio", "")),
        "territorio":       str(row.get("territorio", "")),
        "lat":              row.get("lat") if pd.notna(row.get("lat")) else None,
        "lon":              row.get("lon") if pd.notna(row.get("lon")) else None,
        "descripcion":      str(row.get("descripcion", "")),
        "google_rating":    row.get("google_rating") if pd.notna(row.get("google_rating", float("nan"))) else None,
        "google_num_reviews": row.get("google_num_reviews") if pd.notna(row.get("google_num_reviews", float("nan"))) else None,
        "web":              str(row.get("web", "")),
        "ficha_turismo":    str(row.get("ficha_turismo", "")),
        "local_ratio": row.get("local_ratio"),
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(csv_path: str, reviews_path: str, output_dir: str):

    os.makedirs(output_dir, exist_ok=True)
    index_path    = os.path.join(output_dir, "faiss_index.index")
    metadata_path = os.path.join(output_dir, "faiss_metadata.json")

    # ── 1. Cargar datos ───────────────────────────────────────────────────────
    print("\n[1/5] Cargando datos...")
    df = pd.read_csv(csv_path)
    print(f"  CSV cargado: {len(df):,} lugares × {len(df.columns)} columnas")

    # Filtrar lugares sin nombre (no son útiles para el chatbot)
    df = df[df["nombre"].notna() & df["nombre"].str.strip().ne("")]
    print(f"  Tras filtro nombre: {len(df):,} lugares")

    # Excluir registros marcados como no aptos para el modelo
    antes = len(df)
    df = df[df["excluir_modelo"] != True]
    print(f"  Excluidos por excluir_modelo: {antes - len(df)} registros")
    print(f"  Registros para indexar: {len(df):,}")

    reviews_by_id = load_reviews(reviews_path)

    # ── 2. Construir textos ───────────────────────────────────────────────────
    print("\n[2/5] Construyendo textos para embeddings...")
    texts = []
    metadata = []

    for _, row in df.iterrows():
        text = build_place_text(row, reviews_by_id)
        texts.append(text)
        metadata.append(build_metadata(row))

    # Muestra de cómo queda un texto (útil para depurar)
    print(f"\n  Ejemplo — texto para embedding del primer lugar:")
    print("  " + "\n  ".join(texts[0].split("\n")))

    n_con_reviews = sum(1 for m in metadata if m["id"] in reviews_by_id)
    print(f"\n  Lugares con reseñas incorporadas: {n_con_reviews:,} / {len(texts):,}")

    # ── 3. Generar embeddings ─────────────────────────────────────────────────
    print(f"\n[3/5] Cargando modelo '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Dimensión de embeddings: {model.get_embedding_dimension()}")

    print(f"\n  Generando embeddings para {len(texts):,} textos...")
    print("  (Esto puede tardar varios minutos en CPU)")
    t0 = time.time()

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,  # necesario para usar similitud coseno con IndexFlatIP
    )

    elapsed = time.time() - t0
    print(f"  Embeddings generados en {elapsed:.1f}s")
    print(f"  Shape: {embeddings.shape}")  # (n_lugares, 384)

    # ── 4. Construir índice FAISS ─────────────────────────────────────────────
    print("\n[4/5] Construyendo índice FAISS...")

    dimension = embeddings.shape[1]

    # IndexFlatIP: búsqueda exacta por producto interior (= coseno con vectores normalizados)
    # Para el volumen que tenemos (~7k lugares) es suficiente y más simple que índices aproximados
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))

    print(f"  Vectores en el índice: {index.ntotal:,}")

    # ── 5. Guardar outputs ────────────────────────────────────────────────────
    print("\n[5/5] Guardando outputs...")

    faiss.write_index(index, index_path)
    print(f"  Índice FAISS: {index_path}  ({os.path.getsize(index_path)//1024} KB)")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"  Metadatos:    {metadata_path}  ({os.path.getsize(metadata_path)//1024} KB)")

    print(f"\n✓ Proceso completado. Outputs en: {output_dir}")
    print(f"  Siguiente paso: usar faiss_index.index + faiss_metadata.json en el backend RAG")


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera embeddings y construye índice FAISS para Txoko RAG")
    parser.add_argument("--csv",        required=True, help="Ruta al CSV principal (aupa_master_v7.csv)")
    parser.add_argument("--reviews",    required=True, help="Ruta al JSON de reseñas (txoko_reviews_raw.json)")
    parser.add_argument("--output-dir", default=".",   help="Directorio donde guardar los outputs (default: .)")
    args = parser.parse_args()

    main(
        csv_path=args.csv,
        reviews_path=args.reviews,
        output_dir=args.output_dir,
    )
