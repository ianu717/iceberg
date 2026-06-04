from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_GeogFromText

from src.db.models import Lugar
from src.api.schemas.api_schemas import Recommendation, RecommendationResponse


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
    top_n: int = 5,
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