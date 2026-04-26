import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.schemas import DashboardStats
from app.cache import cache_get, cache_set
from app.services.dashboard_service import get_dashboard_stats
from app.ml.dial import generate_insights_sync

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
_executor = ThreadPoolExecutor(max_workers=1)
_insights_cache: dict = {}
_INSIGHTS_TTL = 3600  # 1 hour


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    cached = await cache_get("dashboard:stats")
    if cached:
        return cached
    stats = await get_dashboard_stats(db)
    await cache_set("dashboard:stats", stats.model_dump(), ttl=3600)
    return stats


@router.get("/insights")
async def dashboard_insights(db: AsyncSession = Depends(get_db)):
    """AI-generated 2-sentence market summary from real dashboard data + Nifty/VIX."""
    now = time.time()
    if _insights_cache.get("ts") and now - _insights_cache["ts"] < _INSIGHTS_TTL:
        return _insights_cache["data"]

    stats = await get_dashboard_stats(db)

    # Fetch market data using the same helper as the live router
    try:
        from app.api.live import _get_market
        market = await _get_market()
    except Exception:
        market = {"nifty_30d_return": 0.0, "vix_current": 15.0}

    loop = asyncio.get_running_loop()
    insight_text = await loop.run_in_executor(
        _executor, generate_insights_sync, stats.model_dump(), market
    )

    result = {
        "insight":      insight_text,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _insights_cache.update({"data": result, "ts": time.time()})
    return result
