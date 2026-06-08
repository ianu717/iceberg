from typing import Annotated

from fastapi import FastAPI, APIRouter, Query, Depends
from sqlalchemy.orm import Session
from src.db.db import get_db
from .schemas.api_schemas import RecommendationResponse
from .service.recomendation_service import recommend_by_profile, recommend_by_category, recommend_nearest
from src.utils import extract_profile_selection
from src.inference.inference import predict_user_profile

api = FastAPI(title="Iceberg API", version="0.1.0")
router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
        categories: Annotated[list[str], Query(min_length=5, max_length=5)],
        longitude: Annotated[float, Query(ge=-180, le=180)],
        latitude: Annotated[float, Query(ge=-90, le=90)],
        db: Annotated[Session, Depends(get_db)]
):
    preferences, duration, companion = extract_profile_selection(categories)
    predicted_profile = predict_user_profile(preferences, duration, companion)
    return recommend_by_profile(db, predicted_profile, latitude, longitude)

@router.get("/recommendations/category", response_model=RecommendationResponse)
def recommendations_category(
        category: Annotated[str, Query()],
        longitude: Annotated[float, Query(ge=-180, le=180)],
        latitude: Annotated[float, Query(ge=-90, le=90)],
        db: Annotated[Session, Depends(get_db)]
):
    return recommend_by_category(db, category, latitude, longitude)

@router.get("/recommendations/nearest", response_model=RecommendationResponse)
def recommendations_nearest(
    db: Annotated[Session, Depends(get_db)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    latitude: Annotated[float, Query(ge=-90, le=90)],
    top_n: Annotated[int, Query(ge=1, le=24)] = 24,
):
    return recommend_nearest(db, latitude, longitude, top_n=top_n)

api.include_router(router)