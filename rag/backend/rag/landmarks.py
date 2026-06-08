"""
landmarks.py
============
Puntos de referencia turísticos de Euskadi con sus coordenadas.

Uso en retrieval.py:
    from .landmarks import LANDMARKS
    from .landmarks import find_landmark

Cuando la query menciona un landmark conocido, se pueden reordenar
los candidatos de FAISS por distancia haversine al punto de referencia.
"""

from math import radians, sin, cos, sqrt, atan2


# ─── Diccionario de landmarks ─────────────────────────────────────────────────
# Clave: términos que pueden aparecer en la query (minúsculas)
# Valor: (latitud, longitud)

LANDMARKS: dict[str, tuple[float, float]] = {

    # ── Bilbao ────────────────────────────────────────────────────────────────
    "guggenheim":           (43.2686, -2.9340),
    "museo guggenheim":     (43.2686, -2.9340),
    "san mamés":            (43.2643, -2.9494),
    "san mames":            (43.2643, -2.9494),
    "casco viejo":          (43.2587, -2.9236),
    "casco viejo bilbao":   (43.2587, -2.9236),
    "catedral de santiago": (43.2571, -2.9246),
    "mercado de la ribera": (43.2559, -2.9230),
    "la ribera":            (43.2559, -2.9230),
    "plaza nueva":          (43.2590, -2.9240),
    "plaza nueva bilbao":   (43.2590, -2.9240),
    "teatro arriaga":       (43.2596, -2.9257),
    "arriaga":              (43.2596, -2.9257),
    "azkuna zentroa":       (43.2638, -2.9382),
    "alhóndiga":            (43.2638, -2.9382),
    "alhondiga":            (43.2638, -2.9382),
    "museo de bellas artes": (43.2682, -2.9396),
    "bellas artes bilbao":  (43.2682, -2.9396),
    "euskalduna":           (43.2666, -2.9453),
    "palacio euskalduna":   (43.2666, -2.9453),
    "torre iberdrola":      (43.2690, -2.9427),
    "iberdrola":            (43.2690, -2.9427),
    "moyúa":                (43.2633, -2.9349),
    "moyua":                (43.2633, -2.9349),
    "plaza moyúa":          (43.2633, -2.9349),
    "plaza moyua":          (43.2633, -2.9349),
    "abando":               (43.2607, -2.9280),
    "estación abando":      (43.2607, -2.9280),
    "ayuntamiento bilbao":  (43.2637, -2.9255),

    # ── Donostia / San Sebastián ──────────────────────────────────────────────
    "la concha":                    (43.3182, -1.9860),
    "playa de la concha":           (43.3182, -1.9860),
    "parte vieja":                  (43.3224, -1.9847),
    "parte vieja donostia":         (43.3224, -1.9847),
    "casco antiguo donostia":       (43.3224, -1.9847),
    "catedral del buen pastor":     (43.3168, -1.9818),
    "buen pastor":                  (43.3168, -1.9818),
    "kursaal":                      (43.3233, -1.9765),
    "palacio kursaal":              (43.3233, -1.9765),
    "peine del viento":             (43.3213, -2.0235),
    "monte igueldo":                (43.3150, -2.0220),
    "igueldo":                      (43.3150, -2.0220),
    "aquarium donostia":            (43.3242, -1.9894),
    "aquarium san sebastián":       (43.3242, -1.9894),
    "miramar":                      (43.3158, -1.9955),
    "palacio miramar":              (43.3158, -1.9955),
    "santa maría del coro":         (43.3230, -1.9853),
    "basílica santa maría":         (43.3230, -1.9853),
    "basilica santa maria":         (43.3230, -1.9853),
    "monte urgull":                 (43.3258, -1.9874),
    "urgull":                       (43.3258, -1.9874),
    "playa de zurriola":            (43.3250, -1.9740),
    "zurriola":                     (43.3250, -1.9740),
    "puerto donostia":              (43.3240, -1.9888),
    "puerto san sebastián":         (43.3240, -1.9888),
    "ayuntamiento donostia":        (43.3214, -1.9839),
    "ayuntamiento san sebastián":   (43.3214, -1.9839),
    "plaza gipuzkoa":               (43.3202, -1.9818),
    "tabakalera":                   (43.3186, -1.9780),

    # ── Vitoria-Gasteiz ───────────────────────────────────────────────────────
    "catedral de santa maría":          (42.8498, -2.6727),
    "catedral santa maria vitoria":     (42.8498, -2.6727),
    "casco medieval vitoria":           (42.8489, -2.6715),
    "casco medieval gasteiz":           (42.8489, -2.6715),
    "plaza de la virgen blanca":        (42.8467, -2.6725),
    "virgen blanca":                    (42.8467, -2.6725),
    "plaza de españa vitoria":          (42.8460, -2.6720),
    "artium":                           (42.8475, -2.6676),
    "museo artium":                     (42.8475, -2.6676),
    "parlamento vasco":                 (42.8455, -2.6710),
    "parque de la florida":             (42.8445, -2.6701),
    "la florida vitoria":               (42.8445, -2.6701),
    "catedral nueva vitoria":           (42.8418, -2.6765),
    "palacio europa":                   (42.8530, -2.6830),
    "estación vitoria":                 (42.8503, -2.6792),
    "estación gasteiz":                 (42.8503, -2.6792),
    "plaza del machete":                (42.8482, -2.6732),
    "muralla medieval vitoria":         (42.8493, -2.6718),
    "ayuntamiento vitoria":             (42.8472, -2.6728),
    "ayuntamiento gasteiz":             (42.8472, -2.6728),
    "salburua":                         (42.8608, -2.6408),
    "parque de salburua":               (42.8608, -2.6408),
}


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos GPS (fórmula haversine)."""
    R = 6_371_000
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def find_landmark(query: str) -> tuple[str, tuple[float, float]] | None:
    """
    Busca si la query menciona algún landmark conocido.

    Devuelve (nombre_landmark, (lat, lon)) si encuentra coincidencia,
    o None si no hay ningún landmark en la query.

    Ejemplo:
        find_landmark("quiero comer cerca del guggenheim")
        → ("guggenheim", (43.2686, -2.9340))
    """
    query_lower = query.lower()
    # Ordenar por longitud descendente para que "museo guggenheim"
    # tenga preferencia sobre "guggenheim"
    for name, coords in sorted(LANDMARKS.items(), key=lambda x: -len(x[0])):
        if name in query_lower:
            return name, coords
    return None


def reorder_by_proximity(
    candidates: list[dict],
    landmark_coords: tuple[float, float],
    max_distance_m: float = 2000,
) -> list[dict]:
    """
    Reordena los candidatos por distancia al landmark.

    Args:
        candidates:      lista de lugares con campos 'lat' y 'lon'
        landmark_coords: (lat, lon) del punto de referencia
        max_distance_m:  radio máximo en metros (default 2km)
                         los lugares fuera del radio se mantienen al final

    Returns:
        Lista reordenada: primero los más cercanos al landmark,
        luego los que no tienen coordenadas o están fuera del radio.
    """
    lat_ref, lon_ref = landmark_coords

    with_distance = []
    without_coords = []

    for place in candidates:
        lat = place.get("lat")
        lon = place.get("lon")
        if lat and lon:
            dist = haversine_m(lat_ref, lon_ref, float(lat), float(lon))
            with_distance.append((dist, place))
        else:
            without_coords.append(place)

    # Ordenar por distancia ascendente
    with_distance.sort(key=lambda x: x[0])

    # Separar los que están dentro del radio
    nearby    = [p for d, p in with_distance if d <= max_distance_m]
    far_away  = [p for d, p in with_distance if d > max_distance_m]

    # Añadir distancia al metadata para que el LLM pueda mencionarla
    for dist, place in with_distance:
        if dist <= max_distance_m:
            place["_distance_m"] = int(dist)

    return nearby + far_away + without_coords
