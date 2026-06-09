"""
build_faiss_index.py
====================
Genera embeddings de los lugares turísticos y construye el índice FAISS.

Inputs:
    - aupa_master_v7.csv         → datos principales de cada lugar
    - txoko_reviews_raw.json     → reseñas de Google (hasta 5 por lugar)

Outputs:
    - faiss_index.index          → índice GLOBAL (todos los lugares)
    - faiss_metadata.json        → metadatos GLOBALES
    
    - faiss_bizkaia.index        → índice solo Bizkaia
    - faiss_metadata_bizkaia.json
    - faiss_gipuzkoa.index       → índice solo Gipuzkoa
    - faiss_metadata_gipuzkoa.json
    - faiss_araba.index          → índice solo Araba
    - faiss_metadata_araba.json

Uso:
    python build_faiss_index.py \
        --csv aupa_master_v7.csv \
        --reviews txoko_reviews_raw.json \
        --output-dir .
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

# más sencillo MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
CSV_TEXT_COLS = ["nombre", "subcategoria", "categoria", "descripcion", "municipio", "territorio"]
MAX_REVIEWS = 5

# Territorios para índices separados
TERRITORIOS = ["BIZKAIA", "GIPUZKOA", "ARABA"]


# ─── Funciones (se mantienen IGUALES) ─────────────────────────────────────────

def build_place_text(row: pd.Series, reviews_by_id: dict) -> str:
    """Construye el texto que se convertirá en embedding para un lugar."""
    parts = []

    parts.append(f"Nombre: {row.get('nombre', '')}")
    parts.append(f"Tipo: {row.get('subcategoria', '')} | {row.get('categoria', '')}")
    parts.append(f"Ubicación: {row.get('municipio', '')}, {row.get('territorio', '')}")

    desc = str(row.get("descripcion", "")).strip()
    if desc and desc != "nan":
        parts.append(f"Descripción: {desc}")

    place_id = str(row.get("id", ""))
    if place_id in reviews_by_id:
        reviews = reviews_by_id[place_id]
        texts = [
            r["text"].strip()
            for r in reviews[:MAX_REVIEWS]
            if r.get("text", "").strip() and r.get("rating", 0) >= 3
        ]
        if texts:
            parts.append("Reseñas: " + " | ".join(texts))

    return "\n".join(parts)


def load_reviews(reviews_path: str) -> dict:
    """Carga el JSON de reseñas."""
    with open(reviews_path, encoding="utf-8") as f:
        raw = json.load(f)

    reviews_by_id = {}
    for place_id, data in raw.items():
        if isinstance(data, dict) and "reviews" in data:
            reviews_by_id[place_id] = data["reviews"]
        elif isinstance(data, list):
            reviews_by_id[place_id] = data

    print(f"  Reseñas cargadas: {len(reviews_by_id)} lugares con reseñas")
    return reviews_by_id


def build_metadata(row: pd.Series) -> dict:
    """Extrae los metadatos que se guardan junto al índice."""
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
        "local_ratio":      row.get("local_ratio"),
    }


def build_index_and_metadata(df, reviews_by_id, model, output_dir, suffix=""):
    """
    Función auxiliar: construye índice y metadatos para un DataFrame dado.
    
    Args:
        df: DataFrame con los lugares
        reviews_by_id: dict de reseñas
        model: SentenceTransformer cargado
        output_dir: directorio de salida
        suffix: sufijo para los nombres de archivo (ej: "_bizkaia")
    
    Returns:
        tuple: (index_path, metadata_path)
    """
    if len(df) == 0:
        print(f"  ⚠️ Sin datos para {suffix or 'global'}, saltando...")
        return None, None
    
    print(f"\n  Generando{' ' + suffix if suffix else ' índice global'}: {len(df):,} lugares...")
    
    # Construir textos y metadatos
    texts = []
    metadata = []
    for _, row in df.iterrows():
        texts.append(build_place_text(row, reviews_by_id))
        metadata.append(build_metadata(row))
    
    # Generar embeddings
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    
    # Construir índice FAISS
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))
    
    # Guardar
    index_name = f"faiss_index{suffix}.index"
    metadata_name = f"faiss_metadata{suffix}.json"
    
    index_path = os.path.join(output_dir, index_name)
    metadata_path = os.path.join(output_dir, metadata_name)
    
    faiss.write_index(index, index_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"    ✓ {index_name} ({index.ntotal} vectores, {os.path.getsize(index_path)//1024} KB)")
    print(f"    ✓ {metadata_name} ({os.path.getsize(metadata_path)//1024} KB)")
    
    return index_path, metadata_path


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(csv_path: str, reviews_path: str, output_dir: str):

    os.makedirs(output_dir, exist_ok=True)

    # ── 1. Cargar datos ───────────────────────────────────────────────────────
    print("\n[1/5] Cargando datos...")
    df = pd.read_csv(csv_path)
    print(f"  CSV cargado: {len(df):,} lugares × {len(df.columns)} columnas")

    # Filtrar lugares sin nombre
    df = df[df["nombre"].notna() & df["nombre"].str.strip().ne("")]
    print(f"  Tras filtro nombre: {len(df):,} lugares")

    # Excluir registros marcados como no aptos para el modelo
    if "excluir_modelo" in df.columns:
        antes = len(df)
        df = df[df["excluir_modelo"] != True]
        print(f"  Excluidos por excluir_modelo: {antes - len(df)} registros")
    
    print(f"  Registros para indexar: {len(df):,}")

    reviews_by_id = load_reviews(reviews_path)

    # ── 2. Cargar modelo (una sola vez, se reutiliza) ─────────────────────────
    print(f"\n[2/5] Cargando modelo '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Dimensión de embeddings: {model.get_sentence_embedding_dimension()}")
    
    # ── 3. Generar índices ────────────────────────────────────────────────────
    print("\n[3/5] Generando índices...")
    
    # 3.1 Índice GLOBAL (todos los lugares) - MANTENEMOS EL EXISTENTE
    build_index_and_metadata(df, reviews_by_id, model, output_dir, suffix="")
    
    # 3.2 Índices por TERRITORIO (NUEVOS)
    print("\n  📍 Generando índices por territorio...")
    for territorio in TERRITORIOS:
        df_territorio = df[df["territorio"] == territorio]
        if len(df_territorio) > 0:
            # Usamos sufijo con el nombre del territorio en minúsculas
            suffix = f"_{territorio.lower()}"
            build_index_and_metadata(df_territorio, reviews_by_id, model, output_dir, suffix=suffix)
        else:
            print(f"\n  ⚠️ No hay lugares en {territorio}, omitiendo índice")

    # ── 4. Resumen final ──────────────────────────────────────────────────────
    print("\n[4/4] Proceso completado.")
    print(f"\n✓ Outputs guardados en: {output_dir}")
    print("\n  Archivos generados:")
    print("    📁 Índice global (compatibilidad):")
    print("       - faiss_index.index")
    print("       - faiss_metadata.json")
    print("\n    📁 Índices por territorio (nuevos):")
    for territorio in TERRITORIOS:
        print(f"       - faiss_{territorio.lower()}.index")
        print(f"       - faiss_metadata_{territorio.lower()}.json")
    print("\n  Uso en backend:")
    print("    - Si detectas territorio en la query → usa índice específico")
    print("    - Si no → usa índice global")


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