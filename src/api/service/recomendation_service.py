from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText

from src.db.models import Lugar
from src.api.schemas.api_schemas import Recommendation, RecommendationResponse

CATEGORY_MAPPING = {
    'food': [
        'Bares de pintxos',
        'Pastelerías y confiterías',
        'Queserías / Conserveras / Productores',
        'Restaurantes / Asadores / Sidrerías',
        'Tiendas gourmet y enotecas',
    ],
    'culture': [
        'Auditorios',
        'Museos y centros de interpretación',
        'Palacios de congresos',
        'Recintos feriales'
    ],
    'nature': [
        'Campings',
        'Centros BTT',
        'Espacios naturales',
        'Rutas y paseos',
    ],
    'bars': [
        'Bares de pintxos'
    ],
    'shopping': [
        'Tiendas gourmet y enotecas',
        'Zonas de compras',
        'Queserías / Conserveras / Productores'
    ],
    'walking_tours': [
        'Rutas y paseos'
    ],
    'family_friendly': [
        'Aquariums',
        'Campings',
        'Centros BTT',
        'Parques de atracciones',
        'Palacios de hielo',
        'Museos y centros de interpretación',
        'Alojamientos rurales'
    ],
    'history': [
        'Cuevas y restos arqueológicos',
        'Edificios religiosos / Castillos',
        'Museos y centros de interpretación'
    ],
    'beaches': [
        'Espacios naturales'# ojo, hay playas y más cosas. hay que buscar en la categoría nombre
    ],
}

def _a_recommendation(lugar: Lugar, distancia_m: float) -> Recommendation:
    """Mapea un Lugar de la BD al schema Recommendation."""
    score = round((lugar.local_ratio or 0) * 100)
    return Recommendation(
        name=lugar.nombre,
        description=lugar.descripcion or "",
        local_score=score,
        category=lugar.subcategoria if lugar.subcategoria else '',
        google_rating=lugar.google_rating or 0,   # sin rating -> 0
        longitude=lugar.lon,
        latitude=lugar.lat,
        distance_from_user=int(distancia_m),
        reviews=[],                                # vacío de momento
    )

def recommend_by_profile(
    db: Session,
    profile: dict,
    lat: float,
    lon: float,
    radio_m: float = 15000,
    top_n: int = 5
) -> RecommendationResponse:

    subcategorias = profile.get("subcategorias", [])

    # Punto del usuario (WKT: lon primero, lat después).
    punto = ST_GeogFromText(f"POINT({lon} {lat})")
    distancia = ST_Distance(Lugar.ubicacion, punto).label("distancia_m")

    recomendaciones = []
    for subcat in subcategorias:
        filas = (
            db.query(Lugar, distancia)
              .filter(Lugar.ubicacion.isnot(None))          # con coords
              .filter(Lugar.subcategoria == subcat)         # de esta subcat
              .filter(ST_DWithin(Lugar.ubicacion, punto, radio_m))  # radio
              .order_by(Lugar.local_ratio.desc().nullslast())  # más local primero
              .limit(top_n)                                  # top N
              .all()
        )
        for lugar, dist in filas:
            recomendaciones.append(_a_recommendation(lugar, dist))

    return RecommendationResponse(recommendations=recomendaciones)

def recommend_by_category_map(
    db: Session,
    category: str,
    lat: float,
    lon: float,
    top_n: int = 20
) -> RecommendationResponse:

    subcategories = CATEGORY_MAPPING[category]
    # Punto del usuario (WKT: lon primero, lat después) y distancia.
    punto = ST_GeogFromText(f"POINT({lon} {lat})")
    distancia = ST_Distance(Lugar.ubicacion, punto).label("distancia_m")

    filas = (
        db.query(Lugar, distancia)
        .filter(Lugar.ubicacion.isnot(None))  # con coords
        .filter(Lugar.subcategoria.in_(subcategories))  # cualquiera de las subcats
        .order_by(distancia.asc())  # más cerca primero
        .limit(top_n)  # top N global
        .all()
    )

    recomendaciones = [_a_recommendation(lugar, dist) for lugar, dist in filas]

    return RecommendationResponse(recommendations=recomendaciones)

def recommend_by_local_score(
    db: Session,
    lat: float,
    lon: float,
    top_n: int = 20,
) -> RecommendationResponse:

    punto = ST_GeogFromText(f"POINT({lon} {lat})")
    distancia = ST_Distance(Lugar.ubicacion, punto).label("distancia_m")

    # FASE 1: top N por local_score (la BD ordena por local_ratio y corta).
    filas = (
        db.query(Lugar, distancia)
        .filter(Lugar.ubicacion.isnot(None))
        #.filter(Lugar.subcategoria.in_(subcategories))
        #.filter(ST_DWithin(Lugar.ubicacion, punto, radio_m))
        .order_by(Lugar.local_ratio.desc().nullslast())  # más local primero
        .limit(top_n)                                     # top N por score
        .all()
    )

    # FASE 2: esos N se reordenan por distancia (en Python, lista pequeña).
    filas_por_distancia = sorted(filas, key=lambda fila: fila[1])  # fila[1] = distancia

    recomendaciones = [_a_recommendation(lugar, dist) for lugar, dist in filas_por_distancia]
    return RecommendationResponse(recommendations=recomendaciones)

def recommend_by_category(
    db: Session,
    category: str,
    lat: float,
    lon: float,
    top_n: int = 20,
) -> RecommendationResponse:

    if category == "local_favorites":
        response = recommend_by_local_score(db, lat, lon, top_n=top_n)
    else:
        response = recommend_by_category_map(db, category, lat, lon, top_n=top_n)

    return response
