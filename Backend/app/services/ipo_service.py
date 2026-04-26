"""
ipo_service.py
Business logic for IPO listing, detail, and comparison.
Routes delegate here; this layer handles DB queries and response assembly.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import Optional
from datetime import date

from app.models.db_models import IPO, FinancialScore, SentimentScore, RiskScore, PeerData, SubscriptionForecast
from app.models.schemas import (
    IPOListResponse, IPOSummary, IPODetail,
    FinancialScoreResponse, SentimentResponse, RiskResponse,
    PeersResponse, SubscriptionResponse, FinancialPillars,
)


def _effective_status(ipo) -> str:
    """
    Compute the correct status from dates rather than trusting the stored value.
    Dates are stored as 'YYYY-MM-DD' strings or None.
    """
    today = date.today().isoformat()
    if ipo.listing_date and ipo.listing_date <= today:
        return "listed"
    if ipo.close_date and ipo.close_date <= today:
        return "listed"
    if ipo.open_date and ipo.open_date <= today:
        if not ipo.close_date or ipo.close_date >= today:
            return "open"
    return ipo.status  # fall back to stored value for live IPOs without dates


def ipo_verdict(confidence_score: float) -> str:
    if confidence_score >= 75:
        return "Strong Buy"
    elif confidence_score >= 60:
        return "Buy"
    elif confidence_score >= 40:
        return "Neutral"
    return "Avoid"


async def get_ipo_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    sector: Optional[str] = None,
    status: Optional[str] = None,
    risk_label: Optional[str] = None,
    sort_by: str = "confidence_score",
) -> IPOListResponse:
    query = select(IPO)
    if sector:
        query = query.where(IPO.sector == sector)
    if status:
        query = query.where(IPO.status == status)
    if risk_label:
        query = query.where(IPO.risk_label == risk_label)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Status priority: open first, then upcoming, then listed
    status_priority = case(
        (IPO.status == "open", 0),
        (IPO.status == "upcoming", 1),
        else_=2,
    )
    sort_col = getattr(IPO, sort_by, IPO.confidence_score)
    query = query.order_by(
        status_priority,
        sort_col.desc().nullslast(),
    ).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    ipos = result.scalars().all()

    return IPOListResponse(
        items=[
            IPOSummary.model_validate(ipo).model_copy(update={"status": _effective_status(ipo)})
            for ipo in ipos
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_ipo_detail(db: AsyncSession, ipo_id: str) -> Optional[IPODetail]:
    ipo = await db.get(IPO, ipo_id)
    if not ipo:
        return None

    fin = (await db.execute(select(FinancialScore).where(FinancialScore.ipo_id == ipo_id))).scalars().first()
    sent = (await db.execute(select(SentimentScore).where(SentimentScore.ipo_id == ipo_id))).scalars().first()
    risk = (await db.execute(select(RiskScore).where(RiskScore.ipo_id == ipo_id))).scalars().first()
    peer = (await db.execute(select(PeerData).where(PeerData.ipo_id == ipo_id))).scalars().first()
    sub = (await db.execute(select(SubscriptionForecast).where(SubscriptionForecast.ipo_id == ipo_id))).scalars().first()

    return IPODetail(
        ipo=IPOSummary.model_validate(ipo).model_copy(update={"status": _effective_status(ipo)}),
        financial=build_financial(ipo_id, fin),
        sentiment=build_sentiment(ipo_id, sent),
        risk=build_risk(ipo_id, risk),
        peers=build_peers(ipo_id, peer),
        subscription=build_subscription(ipo_id, sub),
        verdict=ipo_verdict(ipo.confidence_score or 0),
    )


async def get_financial(db: AsyncSession, ipo_id: str) -> Optional[FinancialScoreResponse]:
    fin = (await db.execute(select(FinancialScore).where(FinancialScore.ipo_id == ipo_id))).scalars().first()
    return build_financial(ipo_id, fin)


async def get_sentiment(db: AsyncSession, ipo_id: str) -> Optional[SentimentResponse]:
    sent = (await db.execute(select(SentimentScore).where(SentimentScore.ipo_id == ipo_id))).scalars().first()
    return build_sentiment(ipo_id, sent)


async def get_risk(db: AsyncSession, ipo_id: str) -> Optional[RiskResponse]:
    risk = (await db.execute(select(RiskScore).where(RiskScore.ipo_id == ipo_id))).scalars().first()
    return build_risk(ipo_id, risk)


async def get_peers(db: AsyncSession, ipo_id: str) -> Optional[PeersResponse]:
    peer = (await db.execute(select(PeerData).where(PeerData.ipo_id == ipo_id))).scalars().first()
    return build_peers(ipo_id, peer)


async def get_subscription(db: AsyncSession, ipo_id: str) -> Optional[SubscriptionResponse]:
    sub = (await db.execute(select(SubscriptionForecast).where(SubscriptionForecast.ipo_id == ipo_id))).scalars().first()
    return build_subscription(ipo_id, sub)


async def get_fraud_flags(db: AsyncSession, ipo_id: str) -> list:
    risk = (await db.execute(select(RiskScore).where(RiskScore.ipo_id == ipo_id))).scalars().first()
    return risk.fraud_flags if risk else []


# --- Response builders ---

def build_financial(ipo_id: str, fin) -> Optional[FinancialScoreResponse]:
    if not fin:
        return None
    return FinancialScoreResponse(
        ipo_id=ipo_id,
        pillars=FinancialPillars(
            profitability=fin.profitability_score or 0,
            growth=fin.growth_score or 0,
            liquidity=fin.liquidity_score or 0,
            solvency=fin.solvency_score or 0,
            efficiency=fin.efficiency_score or 0,
            overall=fin.overall_score or 0,
        ),
        raw_features=fin.raw_features,
    )


def build_sentiment(ipo_id: str, sent) -> Optional[SentimentResponse]:
    if not sent:
        return None
    return SentimentResponse(
        ipo_id=ipo_id,
        score=sent.score or 0,
        label=sent.label or "neutral",
        positive_pct=sent.positive_pct or 0,
        neutral_pct=sent.neutral_pct or 0,
        negative_pct=sent.negative_pct or 0,
        top_keywords=sent.top_keywords or [],
        news_volume_7d=sent.news_volume_7d or 0,
    )


def build_risk(ipo_id: str, risk) -> Optional[RiskResponse]:
    if not risk:
        return None
    return RiskResponse(
        ipo_id=ipo_id,
        risk_score=risk.risk_score or 0,
        risk_label=risk.risk_label or "Medium",
        prob_low=risk.prob_low or 0,
        prob_medium=risk.prob_medium or 0,
        prob_high=risk.prob_high or 0,
        shap_top_drivers=risk.shap_top_drivers or [],
        fraud_flags=risk.fraud_flags or [],
    )


def build_peers(ipo_id: str, peer) -> Optional[PeersResponse]:
    if not peer:
        return None
    return PeersResponse(
        ipo_id=ipo_id,
        ipo_pe=peer.ipo_pe,
        peer_pe_median=peer.peer_pe_median,
        peer_ev_ebitda_median=peer.peer_ev_ebitda_median,
        valuation_label=peer.valuation_label or "Fair",
        peers=peer.peers or [],
    )


def build_subscription(ipo_id: str, sub) -> Optional[SubscriptionResponse]:
    if not sub:
        return None
    return SubscriptionResponse(
        ipo_id=ipo_id,
        qib_predicted=sub.qib_predicted or 0,
        hni_predicted=sub.hni_predicted or 0,
        rii_predicted=sub.rii_predicted or 0,
        overall_predicted=sub.overall_predicted or 0,
        allotment_probability=sub.allotment_probability or 0,
    )
