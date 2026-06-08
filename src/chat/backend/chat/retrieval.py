"""
Retrieval: encode query → FAISS search → filtro post-retrieval → top-k final.
"""

import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from .config import FAISS_TOP_K, FINAL_TOP_K
from .landmarks import find_landmark, reorder_by_proximity


# ── Encoding ───────────────────────────────────────────────────────────────

def encode_query(query: str, model: SentenceTransformer) -> np.ndarray:
    """Devuelve el embedding de la query como array float32 (1, dim)."""
    vector = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    return vector.astype("float32")


# ── FAISS search ───────────────────────────────────────────────────────────

def search_faiss(
    query_vector: np.ndarray,
    index: faiss.Index,
    metadata: list[dict],
    k: int = FAISS_TOP_K,
) -> list[dict]:
    """Devuelve los k candidatos más similares con su metadata."""
    distances, indices = index.search(query_vector, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:          # FAISS devuelve -1 cuando no hay suficientes vectores
            continue
        entry = metadata[idx].copy()
        entry["_score"] = float(dist)
        results.append(entry)

    return results


# ── Filtro post-retrieval ──────────────────────────────────────────────────

def _extract_municipio(query: str) -> str | None:
    """
    Intenta extraer un nombre de municipio de la query.
    Lista de municipios principales de Euskadi.
    Ampliar según necesidades del proyecto.
    """
    MUNICIPIOS = [
        "bilbao", "donostia", "san sebastián", "san sebastian",
        "vitoria", "gasteiz", "vitoria-gasteiz",
        "barakaldo", "getxo", "irun", "eibar", "zarautz",
        "hondarribia", "bermeo", "gernika", "lekeitio",
        "durango", "arrasate", "mondragón", "ondarroa",
        "zumarraga", "azpeitia", "tolosa", "beasain",
        "laudio", "amurrio", "llodio",
    ]
    query_lower = query.lower()
    for m in MUNICIPIOS:
        # búsqueda de palabra completa para evitar falsos positivos
        if re.search(rf"\b{re.escape(m)}\b", query_lower):
            return m
    return None

def _extract_territorio(query: str) -> str | None:

    TERRITORIOS = {
    "gipuzkoa": "GIPUZKOA",
    "guipúzcoa": "GIPUZKOA", 
    "guipuzcoa": "GIPUZKOA",
    "bizkaia": "BIZKAIA",
    "vizcaya": "BIZKAIA",
    "araba": "ARABA",
    "álava": "ARABA",
    "alava": "ARABA",
}
    query_lower = query.lower()
    for term, territorio in TERRITORIOS.items():
        if re.search(rf"\b{re.escape(term)}\b", query_lower):
            return territorio
    return None

def apply_filters(candidates: list[dict], query: str) -> list[dict]:
    
    # Prioridad 1: landmark (más específico)
    landmark = find_landmark(query)
    if landmark:
        _, coords = landmark
        candidates = reorder_by_proximity(candidates, coords)
        return candidates[:FINAL_TOP_K]
    
    # Prioridad 2: municipio concreto
    municipio = _extract_municipio(query)
    if municipio:
        filtered = [c for c in candidates if municipio in (c.get("municipio") or "").lower()]
        if len(filtered) >= 2:
            return filtered[:FINAL_TOP_K]
    
    # Prioridad 3: territorio (Gipuzkoa, Bizkaia, Araba)
    territorio = _extract_territorio(query)
    if territorio:
        filtered = [c for c in candidates if (c.get("territorio") or "").upper() == territorio]
        if len(filtered) >= 2:
            return filtered[:FINAL_TOP_K]
    
    # Sin filtro geográfico: devolver por score semántico
    return candidates[:FINAL_TOP_K]

    


# ── Función principal de retrieval ─────────────────────────────────────────

def retrieve(
    query: str,
    model: SentenceTransformer,
    index: faiss.Index,
    metadata: list[dict],
) -> list[dict]:
    """
    Pipeline completo: encode → FAISS search → filtros → top-k final.
    Devuelve lista de hasta FINAL_TOP_K lugares.
    """
    vector     = encode_query(query, model)
    candidates = search_faiss(vector, index, metadata, k=FAISS_TOP_K)
        # DEBUG
    print(f"DEBUG antes de filtro: {len(candidates)} candidatos")
    for c in candidates:
        print(f"  score={c['_score']:.3f} | {c.get('nombre')} — {c.get('municipio')}")
    
    result = apply_filters(candidates, query)
    print(f"DEBUG tras filtro: {len(result)} candidatos")
    return result
    
