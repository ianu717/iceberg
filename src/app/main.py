from typing import Annotated

from fastapi import FastAPI, APIRouter, Query
from .schemas.api_schemas import RecommendationResponse, Recommendation

mock_response = RecommendationResponse(
    recommendations=[
        Recommendation(
            name="Museo Guggenheim Bilbao",
            description="Museo de arte moderno y contemporáneo diseñado por Frank Gehry, icono de la ciudad.",
            local_score=95,
            google_rating=4.7,
            longitude=-2.9340,
            latitude=43.2687,
            distance_from_user=320.5,
            reviews=[
                "Una obra maestra de la arquitectura, imprescindible.",
                "Las exposiciones rotan y siempre hay algo nuevo que ver.",
                "El Puppy de flores en la entrada es espectacular.",
            ],
        ),
        Recommendation(
            name="Mercado de la Ribera",
            description="Mercado cubierto a orillas de la ría, referencia gastronómica con pintxos y producto local.",
            local_score=88,
            google_rating=4.5,
            longitude=-2.9234,
            latitude=43.2569,
            distance_from_user=1150.0,
            reviews=[
                "Producto fresco y ambiente auténtico.",
                "Los pintxos de la planta de arriba están de muerte.",
            ],
        ),
        Recommendation(
            name="Casco Viejo (Las Siete Calles)",
            description="Núcleo histórico de Bilbao, ideal para pasear entre comercios, bares y arquitectura tradicional.",
            local_score=82,
            google_rating=4.6,
            longitude=-2.9230,
            latitude=43.2560,
            distance_from_user=1280.3,
            reviews=[
                "Perfecto para perderse y descubrir rincones.",
                "Zona ideal para el txikiteo de tarde.",
                "Muy animado los fines de semana.",
            ],
        ),
        Recommendation(
            name="Puente de La Salve",
            description="Puente sobre la ría junto al Guggenheim, con la icónica estructura roja de Daniel Buren.",
            local_score=70,
            google_rating=4.4,
            longitude=-2.9325,
            latitude=43.2695,
            distance_from_user=410.8,
            reviews=[
                "Las vistas al museo desde aquí son geniales.",
            ],
        ),
        Recommendation(
            name="Azkuna Zentroa (Alhóndiga)",
            description="Centro cultural y de ocio rehabilitado por Philippe Starck, con cine, piscina y gastronomía.",
            local_score=78,
            google_rating=4.5,
            longitude=-2.9370,
            latitude=43.2603,
            distance_from_user=890.2,
            reviews=[
                "Las 43 columnas del vestíbulo son una pasada.",
                "Buen plan con niños y para resguardarse si llueve.",
            ],
        ),
    ]
)

app = FastAPI(title=" API", version="0.1.0")
router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
    categories: Annotated[list[str], Query()],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    latitude: Annotated[float, Query(ge=-90, le=90)]
):
    print(categories)
    print(longitude)
    print(latitude)
    return mock_response

@router.get("/inference/filter")
def inference_filter(category: str, longitude: float, latitude: float):
    return

app.include_router(router)