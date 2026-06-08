"""
Construcción del prompt que se envía al LLM.
"""

from .config import SYSTEM_PROMPT
from langdetect import detect, LangDetectException


def _format_place(i: int, place: dict) -> str:
    """Formatea un lugar como bloque de texto numerado."""
    
    # Extraer campos del diccionario de metadatos
    nombre      = place.get("nombre", "Sin nombre")
    municipio   = place.get("municipio", "")
    provincia   = place.get("provincia", "")
    categoria   = place.get("categoria") or place.get("categoría", "")
    descripcion = place.get("descripcion") or place.get("descripción", "Sin descripción")
    rating      = place.get("google_rating")
    num_reviews = place.get("google_num_reviews")
    local_ratio = place.get("local_ratio")
    distance    = place.get("_distance_m")  # añadido por landmarks.py

    ubicacion = ", ".join(filter(None, [municipio, provincia]))

    # Construir el bloque de texto línea a línea
    # lines tiene que existir ANTES de hacer append
    lines = [f"{i}. {nombre} — {ubicacion} ({categoria})"]
    lines.append(f"   Descripción: {descripcion}")

    if rating is not None:
        review_str = f" ({int(num_reviews)} reseñas)" if num_reviews else ""
        lines.append(f"   Rating: {rating}{review_str}")

    
    if local_ratio is not None:
        local_label = f"{int(float(local_ratio) * 100)}/100"
        lines.append(f"   Autenticidad local: {local_label}")

    # Distancia al landmark si la consulta es geográfica
    if distance is not None:
        lines.append(f"   Distancia al punto de referencia: {distance}m")

    return "\n".join(lines)

def build_prompt(query: str, places: list[dict]) -> tuple[str, str]:
    
    # Detectar idioma de la query
    try:
        lang = detect(query)
    except LangDetectException:
        lang = "es"  # fallback castellano
    
    if lang == "en":
        lang_instruction = "IMPORTANT: The user is writing in English. You MUST respond in English."
    elif lang == "eu":
        lang_instruction = "GARRANTZITSUA: Erabiltzaileak euskaraz idazten du. Erantzun euskaraz."
    else:
        lang_instruction = "IMPORTANTE: El usuario escribe en español. Responde en español."


    places_block = "\n\n".join(
        _format_place(i + 1, p) for i, p in enumerate(places)
    )

    user_section = (
        f"{lang_instruction}\n\n"
        f'El usuario pregunta: "{query}"\n\n'
        f"Lugares disponibles:\n\n"
        f"{places_block}"
    )

    return user_section, SYSTEM_PROMPT  # devuelve tupla


