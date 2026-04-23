from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.schemas import (
    RecommendationRequest, RecommendationResponse,
    InvestorProfileRequest, InvestorProfileResponse,
)
from app.services.recommendation_service import get_recommendations, upsert_profile, fetch_profile

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.post("/recommendations", response_model=RecommendationResponse)
async def post_recommendations(req: RecommendationRequest, db: AsyncSession = Depends(get_db)):
    return await get_recommendations(db, req)


@router.post("/profile", response_model=InvestorProfileResponse)
async def post_profile(req: InvestorProfileRequest, db: AsyncSession = Depends(get_db)):
    return await upsert_profile(db, req)


@router.get("/profile/{user_id}", response_model=InvestorProfileResponse)
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    profile = await fetch_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
