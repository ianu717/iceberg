"""
Carga en memoria el índice FAISS y los metadatos asociados.
Se llama una sola vez al arrancar el servidor (lifespan).
"""

import json
import faiss
from pathlib import Path

from .config import FAISS_INDEX_PATH, FAISS_METADATA_PATH
from .config import FAISS_INDEX_PATH

def load_faiss_index(index_path: Path = FAISS_INDEX_PATH) -> faiss.Index:
    if not index_path.exists():
        raise FileNotFoundError(f"FAISS index not found: {index_path}")
    return faiss.read_index(str(index_path))


def load_metadata(metadata_path: Path = FAISS_METADATA_PATH) -> list[dict]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)
