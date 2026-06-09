"""
Retrieval: encode query → FAISS search → filtro post-retrieval → top-k final.
 
Lógica de filtrado (prioridad decreciente):
  1. landmark  → solo lugares a ≤1km del landmark, dentro de su municipio
  2. municipio → solo lugares de ese municipio
  3. territorio → todos los lugares del territorio (índice territorial)
  4. sin filtro → índice global, orden por score semántico
"""

import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from .config import FAISS_TOP_K, FINAL_TOP_K
from .landmarks import find_landmark, reorder_by_proximity

# Predefinición categorías

MUNICIPIOS = [
        "bilbao", "donostia", "san sebastián", "san sebastian",
        "vitoria", "gasteiz", "vitoria-gasteiz",
        "barakaldo", "getxo", "irun", "eibar", "zarautz",
        "hondarribia", "bermeo", "gernika", "lekeitio",
        "durango", "arrasate", "mondragón", "ondarroa",
        "zumarraga", "azpeitia", "tolosa", "beasain",
        "laudio", "amurrio", "llodio",
    ]
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

BILBAO_LANDMARKS = [
    "guggenheim", "san mamés", "casco viejo", "mercado de la ribera",
    "plaza nueva", "teatro arriaga", "azkuna zentroa", "euskalduna",
    "torre iberdrola", "moyua", "abando", "ayuntamiento bilbao",
    "museo de bellas artes"
]
DONOSTIA_LANDMARKS = [
    "la concha", "parte vieja", "kursaal", "peine del viento",
    "monte igueldo", "monte urgull", "zurriola", "tabakalera",
    "miramar", "buen pastor"
]
VITORIA_LANDMARKS = [
    "artium", "virgen blanca", "catedral de santa maría",
    "parlamento vasco", "palacio europa", "salburua"
]

MUNICIPIO_A_TERRITORIO = {
    # Bizkaia
    "bilbao":    "bizkaia",
    "barakaldo": "bizkaia",
    "getxo":     "bizkaia",
    "bermeo":    "bizkaia",
    "gernika":   "bizkaia",
    "lekeitio":  "bizkaia",
    "durango":   "bizkaia",
    "ondarroa":  "bizkaia",
    "eibar":     "bizkaia",
    "mungia":    "bizkaia",
    "amorebieta":"bizkaia",
    "erandio":   "bizkaia",
    "sestao":    "bizkaia",
    "portugalete": "bizkaia",
    "santurtzi": "bizkaia",
    "basauri":   "bizkaia",
    "galdakao":  "bizkaia",
    "leioa":     "bizkaia",
    "bakio":     "bizkaia",
    "plentzia":  "bizkaia",
    "mundaka":   "bizkaia",
    "sopelana":  "bizkaia",
    "barrika":   "bizkaia",
    # Gipuzkoa
    "donostia":      "gipuzkoa",
    "san sebastián": "gipuzkoa",
    "san sebastian": "gipuzkoa",
    "irun":          "gipuzkoa",
    "zarautz":       "gipuzkoa",
    "hondarribia":   "gipuzkoa",
    "tolosa":        "gipuzkoa",
    "azpeitia":      "gipuzkoa",
    "beasain":       "gipuzkoa",
    "zumarraga":     "gipuzkoa",
    "arrasate":      "gipuzkoa",
    "mondragón":     "gipuzkoa",
    "bergara":       "gipuzkoa",
    "zumaia":        "gipuzkoa",
    "deba":          "gipuzkoa",
    "mutriku":       "gipuzkoa",
    "orio":          "gipuzkoa",
    "getaria":       "gipuzkoa",
    "pasaia":        "gipuzkoa",
    "hernani":       "gipuzkoa",
    # Araba
    "vitoria":        "araba",
    "gasteiz":        "araba",
    "vitoria-gasteiz":"araba",
    "laudio":         "araba",
    "amurrio":        "araba",
    "llodio":         "araba",
    "salvatierra":    "araba",
    "agurain":        "araba",
}

LANDMARK_A_MUNICIPIO = {
    # Bilbao
    "guggenheim":            "bilbao",
    "museo guggenheim":      "bilbao",
    "san mamés":             "bilbao",
    "san mames":             "bilbao",
    "casco viejo":           "bilbao",
    "mercado de la ribera":  "bilbao",
    "la ribera":             "bilbao",
    "plaza nueva":           "bilbao",
    "teatro arriaga":        "bilbao",
    "arriaga":               "bilbao",
    "azkuna zentroa":        "bilbao",
    "alhóndiga":             "bilbao",
    "alhondiga":             "bilbao",
    "museo de bellas artes": "bilbao",
    "bellas artes bilbao":   "bilbao",
    "euskalduna":            "bilbao",
    "palacio euskalduna":    "bilbao",
    "torre iberdrola":       "bilbao",
    "iberdrola":             "bilbao",
    "moyúa":                 "bilbao",
    "moyua":                 "bilbao",
    "ayuntamiento bilbao":   "bilbao",
    "catedral de santiago":  "bilbao",
    # Donostia
    "la concha":             "donostia",
    "playa de la concha":    "donostia",
    "parte vieja":           "donostia",
    "kursaal":               "donostia",
    "peine del viento":      "donostia",
    "monte igueldo":         "donostia",
    "igueldo":               "donostia",
    "monte urgull":          "donostia",
    "urgull":                "donostia",
    "zurriola":              "donostia",
    "tabakalera":            "donostia",
    "miramar":               "donostia",
    "buen pastor":           "donostia",
    "aquarium donostia":     "donostia",
    # Vitoria
    "artium":                "vitoria",
    "museo artium":          "vitoria",
    "virgen blanca":         "vitoria",
    "catedral de santa maría":"vitoria",
    "parlamento vasco":      "vitoria",
    "palacio europa":        "vitoria",
    "salburua":              "vitoria",
    "parque de salburua":    "vitoria",
}
CATEGORIA_KEYWORDS = {
        ("Culinario",): ["comer", "cenar", "restaurante", "pintxos", "sidrería", "bar", "eat", "food", "dinner"],
        ("Alojamiento",): ["dormir", "hotel", "alojamiento", "hostal", "sleep", "stay"],
        ("Cultural",): ["museo", "arte", "cultura", "museum", "art"],
        ("Naturaleza", "Servicios"): ["ruta", "rutas", "senderismo", "hiking", "hike", "paseo"],
        ("Naturaleza",): ["playa", "beach", "parque natural"],
        ("Ocio",): ["actividad", "deporte", "surf", "kayak", "activity"],
    }

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
   
    query_lower = query.lower()
    for m in MUNICIPIOS:
        # búsqueda de palabra completa para evitar falsos positivos
        if re.search(rf"\b{re.escape(m)}\b", query_lower):
            return m
    return None

def _extract_territorio(query: str) -> str | None:


    query_lower = query.lower()
    for term, territorio in TERRITORIOS.items():
        if re.search(rf"\b{re.escape(term)}\b", query_lower):
            return territorio
    return None

def _territorio_from_landmark(landmark_name: str) -> str | None:
    name = landmark_name.lower()
    if any(l in name for l in BILBAO_LANDMARKS):
        return "BIZKAIA"
    if any(l in name for l in DONOSTIA_LANDMARKS):
        return "GIPUZKOA"
    if any(l in name for l in VITORIA_LANDMARKS):
        return "ARABA"
    return None

def _extract_categoria(query: str) -> str | None:
    query_lower = query.lower()
    for categorias, keywords in CATEGORIA_KEYWORDS.items():
        if any(k in query_lower for k in keywords):
            return list(categorias)
    return None
# Sustituido
# def apply_filters(candidates: list[dict], query: str) -> list[dict]:
    
#     # Prioridad 1: landmark (más específico)
#     landmark = find_landmark(query)
#     if landmark:
#         _, coords = landmark
#         candidates = reorder_by_proximity(candidates, coords)
#         return candidates[:FINAL_TOP_K]
    
#     # Prioridad 2: municipio concreto
#     municipio = _extract_municipio(query)
#     if municipio:
#         filtered = [c for c in candidates if municipio in (c.get("municipio") or "").lower()]
#         if len(filtered) >= 2:
#             return filtered[:FINAL_TOP_K]
    
#     # Prioridad 3: territorio (Gipuzkoa, Bizkaia, Araba)
#     territorio = _extract_territorio(query)
#     if territorio:
#         filtered = [c for c in candidates if (c.get("territorio") or "").upper() == territorio]
#         if len(filtered) >= 2:
#             return filtered[:FINAL_TOP_K]
    
#     # Sin filtro geográfico: devolver por score semántico
#     return candidates[:FINAL_TOP_K]

    


# ── Función principal de retrieval ─────────────────────────────────────────

def retrieve(query, model, indexes, k=50):
    vector = encode_query(query, model)
    
    # Decidir qué índice usar
    territorio = _extract_territorio(query)
    municipio  = _extract_municipio(query)
    landmark   = find_landmark(query)
    categoria  = _extract_categoria(query)
    
    
    # Inferir municipio desde landmark si no hay municipio explícito
    if landmark and not municipio:
        nombre_landmark, _ = landmark
        municipio = LANDMARK_A_MUNICIPIO.get(nombre_landmark)
    
    # Inferir territorio desde municipio si no hay territorio explícito
    if municipio and not territorio:
        territorio = MUNICIPIO_A_TERRITORIO.get(municipio)

    # Seleccionar índice
    if territorio and territorio.lower() in indexes:
        idx      = indexes[territorio.lower()]["index"]
        metadata = indexes[territorio.lower()]["metadata"]
        print(f"DEBUG usando índice: {territorio}")
    else:
        idx      = indexes["all"]["index"]
        metadata = indexes["all"]["metadata"]
        print(f"DEBUG usando índice: all")
    
    # Buscar
    distances, indices = idx.search(vector, k)
    candidates = []
    for dist, i in zip(distances[0], indices[0]):
        if i == -1:
            continue
        entry = metadata[i].copy()
        entry["_score"] = float(dist)
        candidates.append(entry)
    
    # 1. Filtro de categoría OBLIGATORIO si se puede inferir
    if categoria:
        filtered = [c for c in candidates if c.get("categoria") in categoria]
        if len(filtered) >= 1:
            candidates = filtered
    
    # 2a. Filtro landmark: municipio + distancia ≤1km
    if landmark:
        nombre_landmark, coords = landmark

        # Primero filtrar por municipio del landmark
        if municipio:
            in_municipio = [
                c for c in candidates
                if municipio in (c.get("municipio") or "").lower()
            ]
            if in_municipio:
                candidates = in_municipio
                print(f"DEBUG filtro municipio landmark '{municipio}': {len(candidates)} resultados")
 
        # Luego reordenar por proximidad y quedarse con los de ≤1km primero
        candidates = reorder_by_proximity(candidates, coords, max_distance_m=1000)
        print(f"DEBUG reordenado por proximidad a '{nombre_landmark}'")
 
    # 2b. Filtro municipio (sin landmark)
    elif municipio:
        filtered = [
            c for c in candidates
            if municipio in (c.get("municipio") or "").lower()
        ]
        if filtered:
            candidates = filtered
            print(f"DEBUG filtro municipio '{municipio}': {len(candidates)} resultados")
 
    return candidates[:FINAL_TOP_K]
 
    
