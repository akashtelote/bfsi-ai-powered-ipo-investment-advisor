from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.schemas import DashboardStats
from app.cache import cache_get, cache_set
from app.services.dashboard_service import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("dashboard:stats")
    if cached:
        return cached
    stats = await get_dashboard_stats(db)
    await cache_set("dashboard:stats", stats.model_dump(), ttl=3600)
    return stats
