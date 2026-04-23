"""
recommendation_service.py
Business logic for IPO recommendations and investor profile management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from app.models.db_models import IPO, InvestorProfile
from app.models.schemas import (
    RecommendationRequest, RecommendationResponse, RecommendationItem,
    IPOSummary, InvestorProfileRequest, InvestorProfileResponse,
)


def compute_suitability(ipo: IPO, req: RecommendationRequest) -> float:
    """Score how well an IPO matches the investor's profile (0-100)."""
    score = ipo.confidence_score or 50.0
    risk_map = {"Low": 1, "Medium": 2, "High": 3}
    ipo_risk = risk_map.get(ipo.risk_label or "Medium", 2)
    # Penalise mismatch between investor's risk tolerance (1-5 -> 1-2.5) and IPO risk (1-3)
    risk_match = 1 - abs(ipo_risk - req.risk_tolerance / 2) / 3
    sector_bonus = 5 if req.preferred_sectors and ipo.sector in req.preferred_sectors else 0
    return min(100.0, score * 0.8 + risk_match * 15 + sector_bonus)


def generate_reasons(ipo: IPO, req: RecommendationRequest) -> list[str]:
    reasons = []
    if ipo.financial_score and ipo.financial_score >= 70:
        reasons.append(f"Strong financial health (score: {ipo.financial_score:.0f}/100)")
    if ipo.sentiment_score and ipo.sentiment_score >= 65:
        reasons.append(f"Positive market sentiment ({ipo.sentiment_score:.0f}/100)")
    if ipo.risk_label == "Low":
        reasons.append("Low risk profile matches your investment criteria")
    if req.preferred_sectors and ipo.sector in req.preferred_sectors:
        reasons.append(f"Preferred sector match: {ipo.sector}")
    if ipo.overall_sub_multiple and ipo.overall_sub_multiple >= 10:
        reasons.append(f"High demand expected ({ipo.overall_sub_multiple:.1f}x subscription)")
    if not reasons:
        reasons.append("Moderate overall score based on ML analysis")
    return reasons[:3]


def suitability_verdict(score: float) -> str:
    if score >= 75:
        return "Strong Buy"
    elif score >= 60:
        return "Buy"
    elif score >= 40:
        return "Neutral"
    return "Avoid"


async def get_recommendations(db: AsyncSession, req: RecommendationRequest) -> RecommendationResponse:
    from app.ml.model_orchestrator import ModelOrchestrator
    import pandas as pd

    query = select(IPO).where(IPO.status.in_(["open", "upcoming"]))
    query = query.order_by(IPO.confidence_score.desc().nullslast()).limit(50)
    result = await db.execute(query)
    ipos = result.scalars().all()

    orchestrator = ModelOrchestrator.get()

    # Use ML model ranking if recommendation model is loaded, else rule-based
    if orchestrator._loaded and "recommendation" in orchestrator._models:
        ipos_data = [
            {
                "id": ipo.id, "company_name": ipo.company_name, "sector": ipo.sector,
                "financial_score": ipo.financial_score or 50,
                "sentiment_score": ipo.sentiment_score or 50,
                "risk_score": ipo.risk_score or 50,
                "confidence_score": ipo.confidence_score or 50,
                "overall_sub_multiple": ipo.overall_sub_multiple or 1,
                "risk_label": ipo.risk_label or "Medium",
            }
            for ipo in ipos
        ]
        df = pd.DataFrame(ipos_data)
        ranked_df = orchestrator.rank_recommendations(df, req.model_dump())
        ipo_map = {ipo.id: ipo for ipo in ipos}
        recs = []
        for _, row in ranked_df.iterrows():
            ipo = ipo_map.get(row["id"])
            if ipo:
                score = float(row.get("suitability_score", compute_suitability(ipo, req)))
                recs.append(RecommendationItem(
                    ipo=IPOSummary.model_validate(ipo),
                    suitability_score=round(score, 1),
                    verdict=suitability_verdict(score),
                    reasons=generate_reasons(ipo, req),
                ))
    else:
        recs = [
            RecommendationItem(
                ipo=IPOSummary.model_validate(ipo),
                suitability_score=round(compute_suitability(ipo, req), 1),
                verdict=suitability_verdict(compute_suitability(ipo, req)),
                reasons=generate_reasons(ipo, req),
            )
            for ipo in ipos
        ]
        recs.sort(key=lambda x: x.suitability_score, reverse=True)

    return RecommendationResponse(
        user_id=req.user_id,
        recommendations=recs[:10],
        generated_at=datetime.utcnow().isoformat(),
    )


async def upsert_profile(db: AsyncSession, req: InvestorProfileRequest) -> InvestorProfileResponse:
    profile = await db.get(InvestorProfile, req.user_id)
    if profile:
        profile.risk_tolerance = req.risk_tolerance
        profile.preferred_sectors = req.preferred_sectors
        profile.investment_horizon = req.investment_horizon
        profile.portfolio_size = req.portfolio_size
        profile.sebi_category = req.sebi_category
    else:
        profile = InvestorProfile(
            user_id=req.user_id,
            risk_tolerance=req.risk_tolerance,
            preferred_sectors=req.preferred_sectors,
            investment_horizon=req.investment_horizon,
            portfolio_size=req.portfolio_size,
            sebi_category=req.sebi_category,
        )
        db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return InvestorProfileResponse.model_validate(profile)


async def fetch_profile(db: AsyncSession, user_id: str) -> Optional[InvestorProfileResponse]:
    profile = await db.get(InvestorProfile, user_id)
    if not profile:
        return None
    return InvestorProfileResponse.model_validate(profile)
