"""
dashboard_service.py
Business logic for KPI dashboard statistics.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.db_models import IPO
from app.models.schemas import DashboardStats, IPOSummary


async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    total = (await db.execute(select(func.count(IPO.id)))).scalar_one()
    open_count = (await db.execute(select(func.count(IPO.id)).where(IPO.status == "open"))).scalar_one()
    upcoming_count = (await db.execute(select(func.count(IPO.id)).where(IPO.status == "upcoming"))).scalar_one()
    listed_count = (await db.execute(select(func.count(IPO.id)).where(IPO.status == "listed"))).scalar_one()

    avg_financial = (await db.execute(select(func.avg(IPO.financial_score)))).scalar_one() or 0
    avg_sentiment = (await db.execute(select(func.avg(IPO.sentiment_score)))).scalar_one() or 0

    high_risk = (await db.execute(select(func.count(IPO.id)).where(IPO.risk_label == "High"))).scalar_one()
    med_risk = (await db.execute(select(func.count(IPO.id)).where(IPO.risk_label == "Medium"))).scalar_one()
    low_risk = (await db.execute(select(func.count(IPO.id)).where(IPO.risk_label == "Low"))).scalar_one()
    strong_buy = (await db.execute(select(func.count(IPO.id)).where(IPO.confidence_score >= 75))).scalar_one()

    top_ipos_result = await db.execute(
        select(IPO).order_by(IPO.confidence_score.desc().nullslast()).limit(5)
    )
    top_ipos = top_ipos_result.scalars().all()

    return DashboardStats(
        total_ipos=total,
        open_ipos=open_count,
        upcoming_ipos=upcoming_count,
        listed_ipos=listed_count,
        avg_financial_score=round(avg_financial, 1),
        avg_sentiment_score=round(avg_sentiment, 1),
        high_risk_count=high_risk,
        medium_risk_count=med_risk,
        low_risk_count=low_risk,
        strong_buy_count=strong_buy,
        top_ipos=[IPOSummary.model_validate(ipo) for ipo in top_ipos],
    )
