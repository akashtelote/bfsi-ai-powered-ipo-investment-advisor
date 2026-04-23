import math
import os
import re
import time
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fastapi import APIRouter, Query
from app.models.schemas import (
    LiveAnalysisRequest, LiveAnalysisResponse,
    SentimentResponse, RiskResponse, SubscriptionResponse, MarketContext,
)
from app.ml.model_orchestrator import ModelOrchestrator

router = APIRouter(prefix="/api/live", tags=["live"])
_executor = ThreadPoolExecutor(max_workers=2)
_market_cache: dict = {}
_CACHE_TTL = 3600  # 1 hour


# ── Market data (yfinance, 1-hour in-memory cache) ────────────────────────────

def _fetch_market_sync() -> dict:
    try:
        import yfinance as yf
        nifty = yf.download("^NSEI", period="35d", progress=False, auto_adjust=True)
        closes = nifty["Close"].dropna()
        if len(closes) >= 30:
            c_last = float(closes.values[-1])
            c_base = float(closes.values[-30])
            nifty_ret = (c_last / c_base - 1) * 100
        else:
            nifty_ret = 0.0
        vix = yf.download("^INDIAVIX", period="2d", progress=False, auto_adjust=True)
        vix_closes = vix["Close"].dropna()
        vix_val = float(vix_closes.values[-1]) if len(vix_closes) > 0 else 15.0
    except Exception:
        nifty_ret, vix_val = 0.0, 15.0
    return {
        "nifty_30d_return": round(nifty_ret, 2),
        "vix_current":      round(vix_val, 2),
        "fetched_at":       datetime.now(timezone.utc).isoformat(),
    }


async def _get_market() -> dict:
    now = time.time()
    if _market_cache.get("ts") and now - _market_cache["ts"] < _CACHE_TTL:
        return _market_cache["data"]
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(_executor, _fetch_market_sync)
    _market_cache.update({"data": data, "ts": time.time()})
    return data


@router.get("/market", response_model=MarketContext)
async def get_market():
    """Current NIFTY 30D return and VIX from yfinance (cached 1 hour)."""
    return await _get_market()


# ── News headlines (Google News RSS via feedparser) ───────────────────────────

def _fetch_headlines_sync(company_name: str) -> list[str]:
    try:
        import re
        import feedparser
        query = quote_plus(f"{company_name} IPO India")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)
        headlines = []
        for entry in feed.entries[:5]:
            title = entry.get("title", "")
            summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:200]
            text = f"{title}. {summary}".strip(". ")
            if text:
                headlines.append(text)
        if headlines:
            return headlines
    except Exception:
        pass
    return [company_name, "IPO India stock market listing"]


async def _get_headlines(company_name: str, override: list[str] | None) -> list[str]:
    if override:
        return [h.strip() for h in override[:5] if h.strip()]
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _fetch_headlines_sync, company_name)


# ── IPO detail lookup (Claude AI extraction) ─────────────────────────────────

_SECTORS = [
    "IT Services", "Fintech", "Healthcare", "E-Commerce", "BFSI",
    "Manufacturing", "Consumer", "Renewable Energy", "Insurance",
    "Logistics", "Automobiles", "EdTech", "Agriculture",
]

def _regex_extract(texts: list[str]) -> dict:
    combined = " ".join(texts)
    result: dict = {}
    m = re.search(r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:crore|cr\.?)', combined, re.IGNORECASE)
    if m:
        result["issue_size_cr"] = float(m.group(1).replace(",", ""))
    m = re.search(r'₹\s*(\d+)\s*[-–to]+\s*(?:₹\s*)?(\d+)', combined)
    if m:
        result["price_band_low"]  = float(m.group(1))
        result["price_band_high"] = float(m.group(2))
    return result


def _lookup_sync(company_name: str, headlines: list[str]) -> dict:
    api_url = os.getenv("DIAL_API_URL", "").rstrip("/")
    api_key = os.getenv("DIAL_API_KEY", "")
    model   = os.getenv("DIAL_MODEL", "gpt-4o")

    if api_url and api_key:
        try:
            import httpx
            sectors_str = "|".join(_SECTORS)
            news_text   = "\n".join(f"- {h}" for h in headlines[:5])
            prompt = (
                f"Based on these news headlines about {company_name} IPO, "
                f"extract the following fields. Use null for any value not clearly mentioned.\n\n"
                f"Headlines:\n{news_text}\n\n"
                f"Return ONLY a valid JSON object (no markdown, no explanation):\n"
                f'{{"sector":"<{sectors_str}>","issue_size_cr":<crore number or null>,'
                f'"price_band_low":<INR number or null>,"price_band_high":<INR number or null>,'
                f'"ofs_pct":<0-100 number or null>,"promoter_stake_pre":<0-100 number or null>}}'
            )
            resp = httpx.post(
                f"{api_url}/chat/completions",
                headers={
                    "Api-Key":       api_key,
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":       model,
                    "messages":    [{"role": "user", "content": prompt}],
                    "max_tokens":  300,
                    "temperature": 0,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            raw  = resp.json()["choices"][0]["message"]["content"].strip()
            raw  = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
            data = json.loads(raw)
            data = {k: v for k, v in data.items() if v is not None}
            return {"source": "dial", **data}
        except Exception:
            pass  # fall through to regex

    extracted = _regex_extract(headlines)
    return {"source": "regex", **extracted}


@router.get("/lookup")
async def lookup_ipo(company: str = Query(..., description="Company name to look up")):
    """Auto-fill IPO details using Claude AI extraction from Google News headlines."""
    headlines = await _get_headlines(company, None)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, _lookup_sync, company, headlines)
    return result


# ── Live analysis endpoint ────────────────────────────────────────────────────

@router.post("/analyze", response_model=LiveAnalysisResponse)
async def analyze_live(req: LiveAnalysisRequest):
    """
    Analyze a new IPO in real time:
    - Fetches live headlines from Google News RSS → FinBERT sentiment
    - Fetches live NIFTY 30D return + VIX from yfinance
    - Runs XGBoost risk model + SHAP, CatBoost subscription, Ridge listing
    """
    # Fetch news and market data concurrently
    headlines, market = await asyncio.gather(
        _get_headlines(req.company_name, req.news_override),
        _get_market(),
    )

    orchestrator = ModelOrchestrator.get()

    # FinBERT on live headlines
    sentiment_raw = orchestrator.get_sentiment_score(req.company_name, texts=headlines)

    # Feature vector — live market context + submitted IPO details
    features = {
        "sentiment_score":    sentiment_raw["score"],
        "ofs_pct":            req.ofs_pct,
        "promoter_stake_pre": req.promoter_stake_pre,
        "log_issue_size_cr":  math.log1p(req.issue_size_cr),
        "nifty_30d_return":   market["nifty_30d_return"],
        "vix_at_open":        market["vix_current"],
    }

    risk_raw     = orchestrator.predict_risk(features)
    sub_raw      = orchestrator.predict_subscription(features)
    listing_gain = orchestrator.predict_listing_gain(features)

    # Confidence: financial_score assumed neutral (50) — pillar data unavailable
    confidence = round(
        0.5 * 50.0
        + 0.3 * sentiment_raw["score"]
        + 0.2 * (100 - risk_raw["risk_score"]),
        1,
    )
    verdict = (
        "Strong Buy" if confidence >= 75 else
        "Buy"        if confidence >= 60 else
        "Neutral"    if confidence >= 40 else
        "Avoid"
    )

    return LiveAnalysisResponse(
        company_name=req.company_name,
        sector=req.sector,
        sentiment=SentimentResponse(ipo_id="live", **sentiment_raw),
        risk=RiskResponse(ipo_id="live", fraud_flags=[], **risk_raw),
        subscription=SubscriptionResponse(ipo_id="live", **sub_raw),
        listing_gain_pct=round(float(listing_gain), 1),
        confidence_score=confidence,
        verdict=verdict,
        market_context=MarketContext(**market),
        news_headlines=headlines,
    )
