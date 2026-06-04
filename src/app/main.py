from typing import Annotated

from fastapi import FastAPI, APIRouter, Query, Depends
from sqlalchemy.orm import Session
from src.db.db import get_db
from .schemas.api_schemas import RecommendationResponse, Recommendation
from src.app.service.recomendation_service import recommend_by_profile
from src.utils import extract_profile_selection
from src.inference.inference import predict_user_profile

app = FastAPI(title=" API", version="0.1.0")
router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
        categories: Annotated[list[str], Query(min_length=5, max_length=5)],
        longitude: Annotated[float, Query(ge=-180, le=180)],
        latitude: Annotated[float, Query(ge=-90, le=90)],
        db: Session = Depends(get_db)
):
    preferences, duration, companion = extract_profile_selection(categories)
    predicted_profile = predict_user_profile(preferences, duration, companion)
    return recommend_by_profile(db, predicted_profile, latitude, longitude)

@router.get("/inference/filter")
def inference_filter(category: str, longitude: float, latitude: float):
    return

app.include_router(router)