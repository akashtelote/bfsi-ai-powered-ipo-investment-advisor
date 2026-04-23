import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.db_models import IPO, FinancialScore
from app.models.schemas import (
    IPOListResponse, IPODetail,
    FinancialScoreResponse, SentimentResponse, RiskResponse,
    PeersResponse, SubscriptionResponse, CompareResponse,
)
from app.cache import cache_get, cache_set
from app.services.ipo_service import (
    get_ipo_list, get_ipo_detail, get_financial, get_sentiment,
    get_risk, get_peers, get_subscription, get_fraud_flags,
)
from app.ml.model_orchestrator import ModelOrchestrator

router = APIRouter(prefix="/api/ipos", tags=["ipos"])


@router.get("", response_model=IPOListResponse)
async def list_ipos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sector: Optional[str] = None,
    status: Optional[str] = None,
    risk_label: Optional[str] = None,
    sort_by: str = Query(default="confidence_score",
                         enum=["confidence_score", "financial_score", "sentiment_score", "issue_size_cr"]),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"ipos:{page}:{page_size}:{sector}:{status}:{risk_label}:{sort_by}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    response = await get_ipo_list(db, page, page_size, sector, status, risk_label, sort_by)
    await cache_set(cache_key, response.model_dump(), ttl=3600)
    return response


@router.get("/compare/multi", response_model=CompareResponse)
async def compare_ipos(
    ids: str = Query(..., description="Comma-separated IPO IDs, max 3"),
    db: AsyncSession = Depends(get_db),
):
    ipo_ids = [i.strip() for i in ids.split(",")][:3]
    details = []
    for ipo_id in ipo_ids:
        detail = await get_ipo_detail(db, ipo_id)
        if detail:
            details.append(detail)
    return CompareResponse(ipos=details)


@router.get("/{ipo_id}", response_model=IPODetail)
async def get_ipo(ipo_id: str, db: AsyncSession = Depends(get_db)):
    detail = await get_ipo_detail(db, ipo_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")
    return detail


@router.get("/{ipo_id}/financial", response_model=FinancialScoreResponse)
async def get_financial_score(ipo_id: str, db: AsyncSession = Depends(get_db)):
    _assert_ipo(await db.get(IPO, ipo_id), ipo_id)
    result = await get_financial(db, ipo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Financial score not computed yet")
    return result


@router.get("/{ipo_id}/sentiment", response_model=SentimentResponse)
async def get_sentiment_score(
    ipo_id: str,
    live: bool = False,
    db: AsyncSession = Depends(get_db),
):
    ipo = await db.get(IPO, ipo_id)
    _assert_ipo(ipo, ipo_id)
    if live:
        texts = [t for t in [ipo.company_name, ipo.sector] if t]
        raw = ModelOrchestrator.get().get_sentiment_score(ipo_id, texts=texts)
        return SentimentResponse(ipo_id=ipo_id, **raw)
    result = await get_sentiment(db, ipo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sentiment score not computed yet")
    return result


@router.get("/{ipo_id}/risk", response_model=RiskResponse)
async def get_risk_score(
    ipo_id: str,
    live: bool = False,
    db: AsyncSession = Depends(get_db),
):
    ipo = await db.get(IPO, ipo_id)
    _assert_ipo(ipo, ipo_id)
    if live:
        fin = (await db.execute(
            select(FinancialScore).where(FinancialScore.ipo_id == ipo_id)
        )).scalars().first()
        features = _risk_features(ipo, fin)
        raw = ModelOrchestrator.get().predict_risk(features)
        return RiskResponse(ipo_id=ipo_id, fraud_flags=[], **raw)
    result = await get_risk(db, ipo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Risk score not computed yet")
    return result


@router.get("/{ipo_id}/peers", response_model=PeersResponse)
async def get_peer_data(ipo_id: str, db: AsyncSession = Depends(get_db)):
    _assert_ipo(await db.get(IPO, ipo_id), ipo_id)
    result = await get_peers(db, ipo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Peer data not computed yet")
    return result


@router.get("/{ipo_id}/subscription", response_model=SubscriptionResponse)
async def get_subscription_forecast(ipo_id: str, db: AsyncSession = Depends(get_db)):
    _assert_ipo(await db.get(IPO, ipo_id), ipo_id)
    result = await get_subscription(db, ipo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Subscription forecast not computed yet")
    return result


@router.get("/{ipo_id}/flags")
async def get_flags(ipo_id: str, db: AsyncSession = Depends(get_db)):
    _assert_ipo(await db.get(IPO, ipo_id), ipo_id)
    flags = await get_fraud_flags(db, ipo_id)
    return {"ipo_id": ipo_id, "flags": flags}


def _assert_ipo(ipo, ipo_id: str):
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")


def _risk_features(ipo, fin) -> dict:
    features = {
        "sentiment_score":    ipo.sentiment_score or 50.0,
        "ofs_pct":            ipo.ofs_pct or 0.0,
        "promoter_stake_pre": ipo.promoter_stake_pre or 0.0,
        "log_issue_size_cr":  math.log1p(ipo.issue_size_cr or 0),
    }
    if fin:
        features.update({
            "profitability_score": fin.profitability_score or 50.0,
            "growth_score":        fin.growth_score or 50.0,
            "liquidity_score":     fin.liquidity_score or 50.0,
            "solvency_score":      fin.solvency_score or 50.0,
            "efficiency_score":    fin.efficiency_score or 50.0,
        })
    return features
