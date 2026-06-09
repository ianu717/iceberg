from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field

class RecommendationQuery(BaseModel):
    categories: Annotated[list[str], Query()]
    longitude: Annotated[float, Query(ge=-180, le=180)]
    latitude: Annotated[float, Query(ge=-90, le=90)]

class Recommendation(BaseModel):
    id: str
    name: str
    description: str
    local_score: int = Field(ge=0,  le=100)
    categories: list[str]
    sub_category: str
    google_rating: float = Field(ge=0, le=5)
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    distance_from_user: int = Field(ge=0, description="Distancia en metros")
    reviews: list[str] = Field(default_factory=list)

class RecommendationResponse(BaseModel):
    recommendations: list[Recommendation] = Field(default_factory=list)