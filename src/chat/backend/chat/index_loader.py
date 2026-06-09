"""
Carga en memoria el índice FAISS y los metadatos asociados.
Se llama una sola vez al arrancar el servidor (lifespan).
"""

import json
import faiss
from pathlib import Path

from .config import FAISS_INDEX_PATH, FAISS_METADATA_PATH

def load_faiss_index(index_path: Path = FAISS_INDEX_PATH) -> faiss.Index:
    if not index_path.exists():
        raise FileNotFoundError(f"FAISS index not found: {index_path}")
    return faiss.read_index(str(index_path))


def load_metadata(metadata_path: Path = FAISS_METADATA_PATH) -> list[dict]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_indexes(assets_dir: Path):
    indexes = {}
    
    # Índice principal
    indexes["all"] = {
        "index": faiss.read_index(str(assets_dir / "faiss_index.index")),
        "metadata": json.load(open(assets_dir / "faiss_metadata.json", encoding="utf-8"))
    }
    
    # Índices por territorio
    for territorio in ["bizkaia", "gipuzkoa", "araba"]:
        idx_path  = assets_dir / f"faiss_index_{territorio}.index"
        meta_path = assets_dir / f"faiss_metadata_{territorio}.json"
        if idx_path.exists():
            indexes[territorio] = {
                "index":    faiss.read_index(str(idx_path)),
                "metadata": json.load(open(meta_path, encoding="utf-8"))
            }
            print(f"  ✓ Índice {territorio}: {indexes[territorio]['index'].ntotal} vectores")
    
    return indexes