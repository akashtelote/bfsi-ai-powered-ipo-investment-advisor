import logging
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
from pydantic import BaseModel

from app.database import SessionLocal
from app.cache import cache_bust
from app.models.db_models import IPO, SentimentScore, RiskScore, SubscriptionForecast
from app.models.schemas import (
    LiveAnalysisRequest, LiveAnalysisResponse,
    SentimentResponse, RiskResponse, SubscriptionResponse, MarketContext,
)
from app.ml.model_orchestrator import ModelOrchestrator
from app.ml.dial import assess_ipo_sync, generate_narrative_sync, filter_candidates_sync, discover_current_ipos_sync

router = APIRouter(prefix="/api/live", tags=["live"])
_executor = ThreadPoolExecutor(max_workers=4)
_market_cache: dict = {}
_CACHE_TTL = 3600  # 1 hour

logger = logging.getLogger(__name__)


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
    loop = asyncio.get_running_loop()
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
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _fetch_headlines_sync, company_name)


# ── IPO detail lookup (LLM / regex extraction) ────────────────────────────────

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
            logger.info("DIAL lookup → company=%s  model=%s  endpoint=%s/chat/completions",
                        company_name, model, api_url)
            resp = httpx.post(
                f"{api_url}/openai/deployments/{model}/chat/completions",
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
            logger.info("DIAL response → status=%d  body=%.500s", resp.status_code, resp.text)
            resp.raise_for_status()
            raw  = resp.json()["choices"][0]["message"]["content"].strip()
            raw  = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
            data = json.loads(raw)
            data = {k: v for k, v in data.items() if v is not None}
            logger.info("DIAL parsed → %s", data)
            return {"source": "dial", **data}
        except Exception as exc:
            logger.warning("DIAL lookup failed for %r: %s", company_name, exc)

    extracted = _regex_extract(headlines)
    logger.info("Regex fallback for %r → %s", company_name, extracted)
    return {"source": "regex", **extracted}


@router.get("/lookup")
async def lookup_ipo(company: str = Query(..., description="Company name to look up")):
    """Auto-fill IPO details using LLM/regex extraction from Google News headlines."""
    headlines = await _get_headlines(company, None)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(_executor, _lookup_sync, company, headlines)
    return result


# ── DB persistence helper ─────────────────────────────────────────────────────

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _infer_status(headlines: list[str]) -> str:
    """Infer open/listed/upcoming from the news headlines for this IPO."""
    combined = " ".join(headlines).lower()
    if any(kw in combined for kw in [
        "listed", "listing price", "listing day", "debut", "market debut",
        "allotment finalised", "allotment finalized", "allotment status",
        "listed on nse", "listed on bse",
    ]):
        return "listed"
    if any(kw in combined for kw in [
        "day 1", "day 2", "day 3", "day 4",
        "subscription open", "open for subscription",
        "bidding open", "ipo open", "opens today",
        "opening today", "currently open", "live subscription",
    ]):
        return "open"
    return "upcoming"


async def _persist_to_db(
    req: LiveAnalysisRequest,
    result: LiveAnalysisResponse,
    headlines: list[str] | None = None,
    status_override: str | None = None,
) -> str:
    """Save a live analysis result into the ipos + score tables. Returns the ipo_id."""
    from sqlalchemy import delete

    ipo_id = f"live_{_slug(req.company_name)}"
    # Determine status with date-first priority:
    #   1. listing_date present → listed
    #   2. Subscription window dates available → derive from dates (beats DIAL/heuristic)
    #   3. DIAL status_override → accept it
    #   4. Keyword heuristic from headlines → fallback
    from datetime import date as _date
    today = _date.today().isoformat()
    if req.listing_date:
        status = "listed"
    elif req.open_date and req.close_date:
        # Dates are authoritative when both are present
        if req.close_date < today:
            status = "listed"
        elif req.open_date <= today:
            status = "open"
        else:
            status = "upcoming"
    elif req.open_date and req.open_date > today:
        # open_date in future → definitely upcoming
        status = "upcoming"
    elif status_override in ("open", "upcoming", "listed"):
        status = status_override
    else:
        status = _infer_status(headlines or result.news_headlines)

    # For listed IPOs, prefer actual listing gain from ipoalerts.in over ML prediction
    final_gain = (
        req.actual_listing_gain_pct
        if req.actual_listing_gain_pct is not None
        else result.listing_gain_pct
    )

    async with SessionLocal() as session:
        # Upsert IPO row
        existing = await session.get(IPO, ipo_id)
        if existing:
            # Never downgrade a listed IPO back to open/upcoming on re-analysis
            if not existing.listing_date and existing.status != "listed":
                existing.status = status
            existing.sentiment_score    = result.sentiment.score
            existing.risk_score         = result.risk.risk_score
            existing.risk_label         = result.risk.risk_label
            existing.confidence_score   = result.confidence_score
            existing.overall_sub_multiple = result.subscription.overall_predicted
            existing.listing_gain_pct   = final_gain
            existing.issue_size_cr      = req.issue_size_cr
            existing.price_band_low     = req.price_band_low
            existing.price_band_high    = req.price_band_high
            existing.ofs_pct            = req.ofs_pct
            existing.promoter_stake_pre = req.promoter_stake_pre
            if req.open_date:    existing.open_date    = req.open_date
            if req.close_date:   existing.close_date   = req.close_date
            if req.listing_date: existing.listing_date = req.listing_date
            if req.listing_price is not None: existing.listing_price = req.listing_price
        else:
            session.add(IPO(
                id                    = ipo_id,
                company_name          = req.company_name,
                sector                = req.sector,
                issue_size_cr         = req.issue_size_cr,
                price_band_low        = req.price_band_low,
                price_band_high       = req.price_band_high,
                ofs_pct               = req.ofs_pct,
                promoter_stake_pre    = req.promoter_stake_pre,
                status                = status,
                open_date             = req.open_date,
                close_date            = req.close_date,
                listing_date          = req.listing_date,
                listing_price         = req.listing_price,
                financial_score       = 50.0,
                sentiment_score       = result.sentiment.score,
                risk_score            = result.risk.risk_score,
                risk_label            = result.risk.risk_label,
                confidence_score      = result.confidence_score,
                overall_sub_multiple  = result.subscription.overall_predicted,
                listing_gain_pct      = final_gain,
            ))

        # Replace child rows (delete + insert to keep it simple)
        for model_cls, col in [
            (SentimentScore, SentimentScore.ipo_id),
            (RiskScore, RiskScore.ipo_id),
            (SubscriptionForecast, SubscriptionForecast.ipo_id),
        ]:
            await session.execute(delete(model_cls).where(col == ipo_id))

        s = result.sentiment
        session.add(SentimentScore(
            ipo_id        = ipo_id,
            score         = s.score,
            label         = s.label,
            positive_pct  = s.positive_pct,
            neutral_pct   = s.neutral_pct,
            negative_pct  = s.negative_pct,
            top_keywords  = s.top_keywords,
            news_volume_7d = s.news_volume_7d,
        ))

        r = result.risk
        session.add(RiskScore(
            ipo_id           = ipo_id,
            risk_score       = r.risk_score,
            risk_label       = r.risk_label,
            prob_low         = r.prob_low,
            prob_medium      = r.prob_medium,
            prob_high        = r.prob_high,
            shap_top_drivers = [d.model_dump() for d in r.shap_top_drivers],
            fraud_flags      = [f.model_dump() for f in r.fraud_flags],
        ))

        sub = result.subscription
        session.add(SubscriptionForecast(
            ipo_id               = ipo_id,
            qib_predicted        = sub.qib_predicted,
            hni_predicted        = sub.hni_predicted,
            rii_predicted        = sub.rii_predicted,
            overall_predicted    = sub.overall_predicted,
            allotment_probability = sub.allotment_probability,
        ))

        await session.commit()

    # Bust all ipos:* and dashboard:* cache keys so the next list request
    # hits the DB and returns the freshly saved IPO.
    await cache_bust("ipos:")
    await cache_bust("dashboard:")

    return ipo_id


# ── Live analysis endpoint ────────────────────────────────────────────────────

@router.post("/analyze", response_model=LiveAnalysisResponse)
async def analyze_live(
    req: LiveAnalysisRequest,
    save: bool = Query(default=False, description="Persist result to DB so it appears on the dashboard"),
):
    """
    Analyze a new IPO in real time:
    - Fetches live headlines from Google News RSS → FinBERT sentiment
    - Fetches live NIFTY 30D return + VIX from yfinance
    - Runs XGBoost risk model + SHAP, CatBoost subscription, Ridge listing
    - Pass ?save=true to persist the result into the dashboard DB
    """
    headlines, market = await asyncio.gather(
        _get_headlines(req.company_name, req.news_override),
        _get_market(),
    )

    orchestrator = ModelOrchestrator.get()

    sentiment_raw = orchestrator.get_sentiment_score(req.company_name, texts=headlines)

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

    # ML baseline (kept for SHAP drivers; unreliable for risk/confidence due to 6-feature gap)
    ml_confidence = round(
        0.5 * 50.0
        + 0.3 * sentiment_raw["score"]
        + 0.2 * (100 - risk_raw["risk_score"]),
        1,
    )
    ml_verdict = (
        "Strong Buy" if ml_confidence >= 75 else
        "Buy"        if ml_confidence >= 60 else
        "Neutral"    if ml_confidence >= 40 else
        "Avoid"
    )

    # DIAL assessment — primary override using company knowledge
    loop = asyncio.get_running_loop()
    dial = await loop.run_in_executor(
        _executor,
        assess_ipo_sync,
        req.company_name, req.sector, headlines,
        risk_raw["risk_score"], sentiment_raw["score"],
        round(float(listing_gain), 1), market,
        req.issue_size_cr, req.price_band_high,
    )

    if dial:
        confidence      = dial["confidence_score"]
        verdict         = dial["verdict"]
        listing_gain    = dial["listing_gain_pct"]
        dial_risk       = dial["risk_label"]
        risk_raw["risk_label"] = dial_risk
        risk_raw["risk_score"] = {"Low": 22.0, "Medium": 50.0, "High": 76.0}[dial_risk]
        _probs = {"Low": (0.65, 0.25, 0.10), "Medium": (0.20, 0.60, 0.20), "High": (0.05, 0.25, 0.70)}
        risk_raw["prob_low"], risk_raw["prob_medium"], risk_raw["prob_high"] = _probs[dial_risk]
        narrative        = dial.get("reasoning") or None
        inferred_status  = dial.get("status")
    else:
        confidence, verdict = ml_confidence, ml_verdict
        narrative = await loop.run_in_executor(
            _executor,
            generate_narrative_sync,
            req.company_name, req.sector, verdict, confidence,
            risk_raw["risk_label"], sentiment_raw["score"],
            round(float(listing_gain), 1), market,
        )
        inferred_status = None

    result = LiveAnalysisResponse(
        company_name     = req.company_name,
        sector           = req.sector,
        sentiment        = SentimentResponse(ipo_id="live", **sentiment_raw),
        risk             = RiskResponse(ipo_id="live", fraud_flags=[], **risk_raw),
        subscription     = SubscriptionResponse(ipo_id="live", **sub_raw),
        listing_gain_pct = round(float(listing_gain), 1),
        confidence_score = confidence,
        verdict          = verdict,
        market_context   = MarketContext(**market),
        news_headlines   = headlines,
    )
    result.ai_narrative = narrative

    if save:
        ipo_id = await _persist_to_db(req, result, headlines, status_override=inferred_status)
        result.sentiment.ipo_id   = ipo_id
        result.risk.ipo_id        = ipo_id
        result.subscription.ipo_id = ipo_id

    return result


# ── Discover current IPOs from Google News ───────────────────────────────────

# Skip words that look like company names but aren't
_DISCOVER_SKIP = {
    "the", "this", "an", "upcoming", "latest", "india", "nse", "bse", "sme",
    "new", "ipo", "mainboard", "know", "check", "heck", "all", "about",
    "here", "discount", "profit", "estimate", "safety", "controls",
}

def _infer_sector(name: str) -> str:
    name_l = name.lower()
    if any(w in name_l for w in ["bank", "finance", "capital", "nbfc", "insurance", "amc", "asset"]):
        return "BFSI"
    if any(w in name_l for w in ["tech", "software", "digital", "data", "it ", "infotech", "system"]):
        return "IT Services"
    if any(w in name_l for w in ["pharma", "health", "medic", "hospital", "biotech", "drug"]):
        return "Healthcare"
    if any(w in name_l for w in ["energy", "solar", "power", "electric", "wind", "renew"]):
        return "Renewable Energy"
    if any(w in name_l for w in ["auto", "motor", "vehicle", "transport", "ev "]):
        return "Automobiles"
    if any(w in name_l for w in ["retail", "consumer", "food", "fashion", "lifestyle"]):
        return "Consumer"
    if any(w in name_l for w in ["fintech", "payment", "wallet", "groww", "zerodha", "coin"]):
        return "Fintech"
    if any(w in name_l for w in ["commerce", "shop", "meesho", "market", "trade"]):
        return "E-Commerce"
    if any(w in name_l for w in ["infra", "construction", "cement", "steel", "manufactur"]):
        return "Manufacturing"
    if any(w in name_l for w in ["edu", "learn", "school", "physics", "wallah", "byju"]):
        return "EdTech"
    return "BFSI"


# Words that appear in company names but not in sentence fragments
_NOISE_WORDS = {
    "arm", "billion", "trillion", "crore", "stake", "shares", "status",
    "law", "firms",
}
# If ANY word in the matched text is in this set it's a headline fragment, not a company name
_SENTENCE_WORDS = {
    "files", "file", "filed", "raise", "raises", "raised", "raising",
    "funds", "registrar", "sites", "site", "drhp", "sebi", "via",
    "nse", "bse", "with", "allotment", "subscription", "listing",
    "price", "open", "close", "subscribe", "investors", "retail",
    "and", "plans", "plan", "set", "seeks", "gets", "secures",
}
_NOISE_PHRASES = {"know all", "heck share", "discount to", "estimate", "law firms", "raise funds"}


def _parse_price_range(s: str) -> tuple[float, float]:
    """Parse '₹100 - ₹120' / '100 to 120' / '100-120' → (100.0, 120.0)."""
    nums = re.findall(r'[\d]+(?:\.\d+)?', str(s).replace(",", ""))
    floats = [float(n) for n in nums]
    if len(floats) >= 2:
        return floats[0], floats[1]
    if len(floats) == 1:
        return floats[0], floats[0]
    return 0.0, 0.0


def _parse_issue_size(s: str) -> float:
    """Parse '₹500.00 Cr' / '1,234 Crores' → 500.0."""
    clean = str(s).replace(",", "")
    m = re.search(r'[\d]+(?:\.\d+)?', clean)
    return float(m.group()) if m else 0.0


def _parse_listing_gain(s: str) -> float | None:
    """Parse '+14.20%' / '-5.40%' / '14.20' → float or None."""
    if not s:
        return None
    try:
        return float(str(s).replace("%", "").replace("+", "").strip())
    except (ValueError, TypeError):
        return None


# 24-hour in-memory cache for ipoalerts.in results — one API hit per day maximum.
_ipoalerts_cache: dict = {}
_IPOALERTS_CACHE_TTL = 86400  # 24 hours


def _fetch_ipoalerts_sync(api_key: str, statuses: tuple[str, ...] = ("open",)) -> list[dict]:
    """
    Fetch IPOs from the ipoalerts.in API (free plan).

    Free-plan constraints:
    - Only status=open is supported; upcoming/listed return HTTP 400
    - 1 item per page; totalPages tells you how many requests you need
    - issueSize, listingGain, listingPrice not provided on free plan
    - listingDate on open IPOs is a data artifact — ignored

    Results are cached for 24 hours so the 25 req/day quota is not wasted on
    repeated discover calls from the frontend.
    """
    # Filter to only the statuses the free plan actually supports
    supported = tuple(s for s in statuses if s == "open")
    if not supported:
        return []

    cache_key = ",".join(supported)
    cached = _ipoalerts_cache.get(cache_key)
    if cached and time.time() - cached["ts"] < _IPOALERTS_CACHE_TTL:
        logger.info("ipoalerts.in cache hit (%d items)", len(cached["data"]))
        return cached["data"]

    try:
        import httpx as _httpx
        results: list[dict] = []
        seen: set[str] = set()
        today = datetime.now(timezone.utc).date().isoformat()

        for status in supported:
            # Fetch page 1 to discover totalPages
            resp = _httpx.get(
                "https://api.ipoalerts.in/ipos",
                params={"status": status, "page": 1},
                headers={"x-api-key": api_key},
                timeout=10.0,
            )
            if not resp.is_success:
                logger.warning("ipoalerts.in status=%s HTTP %d: %s",
                               status, resp.status_code, resp.text[:120])
                continue
            data = resp.json()
            total_pages = int((data.get("meta") or {}).get("totalPages") or 1)
            pages_data = [data]

            for page in range(2, total_pages + 1):
                time.sleep(1.2)  # free plan: ~1 req/sec
                pr = _httpx.get(
                    "https://api.ipoalerts.in/ipos",
                    params={"status": status, "page": page},
                    headers={"x-api-key": api_key},
                    timeout=10.0,
                )
                if pr.status_code == 429:
                    logger.warning("ipoalerts.in rate-limited at page %d — stopping", page)
                    break
                if pr.is_success:
                    pages_data.append(pr.json())

            logger.info("ipoalerts.in status=%s: fetched %d pages", status, len(pages_data))

            for page_data in pages_data:
                for item in (page_data.get("ipos") or []):
                    name = (item.get("name") or "").strip()
                    if not name or name.lower() in seen:
                        continue
                    seen.add(name.lower())
                    low, high  = _parse_price_range(item.get("priceRange", ""))
                    size       = _parse_issue_size(item.get("issueSize") or "")
                    open_date  = item.get("startDate")
                    close_date = item.get("endDate")

                    # ipoalerts.in sometimes carries a stale listingDate on open IPOs
                    # (e.g. a parent company's old listing).  Only trust it for listed status.
                    raw_ld = item.get("listingDate")
                    if status == "listed" and raw_ld and raw_ld >= today:
                        listing_date = raw_ld
                    else:
                        listing_date = None

                    results.append({
                        "company_name":   name,
                        "sector":         _infer_sector(name),
                        "price_band_low":  low,
                        "price_band_high": high,
                        "issue_size_cr":   size,
                        "open_date":       open_date,
                        "close_date":      close_date,
                        "listing_date":    listing_date,
                        "listing_price":   None,
                        "actual_listing_gain_pct": None,
                        "status":          status,
                        "source":          "ipoalerts",
                    })

        logger.info("ipoalerts.in total fetched: %d", len(results))
        _ipoalerts_cache[cache_key] = {"data": results, "ts": time.time()}
        return results
    except Exception as exc:
        logger.warning("ipoalerts.in fetch failed: %s", exc)
        return []


def _discover_rss() -> list[dict]:
    """Fallback: scan Google News RSS when no ipoalerts.in API key is configured."""
    queries = [
        "IPO subscription open India NSE after:2026-04-01",
        "IPO allotment listing India BSE after:2026-04-01",
        "SME IPO NSE BSE subscription 2026 after:2026-04-01",
    ]
    name_pat = re.compile(r"([A-Z][A-Za-z0-9\s&\.\-]{2,45}?)\s+IPO\b")
    seen: set[str] = set()
    candidates: list[dict] = []
    try:
        import feedparser
        for query in queries:
            url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                for m in name_pat.finditer(title):
                    name = m.group(1).strip().rstrip("-– ")
                    key  = name.lower().strip()
                    name_words = set(key.split())
                    if (
                        key not in _DISCOVER_SKIP
                        and len(name) >= 3
                        and len(name) <= 50
                        and len(name.split()) <= 5
                        and name[-1] not in "-–,"
                        and not any(phrase in key for phrase in _NOISE_PHRASES)
                        and not any(w in key.split() for w in _NOISE_WORDS)
                        and not name_words.intersection(_SENTENCE_WORDS)
                        and key not in seen
                    ):
                        seen.add(key)
                        candidates.append({
                            "company_name": name,
                            "sector":       _infer_sector(name),
                            "source":       "rss",
                        })
    except Exception:
        pass

    # Use DIAL to remove sentence fragments / non-company strings
    if candidates:
        raw_names = [c["company_name"] for c in candidates]
        filtered_names = filter_candidates_sync(raw_names)
        filtered_set = set(n.lower() for n in filtered_names)
        candidates = [c for c in candidates if c["company_name"].lower() in filtered_set]

    return candidates[:20]


def _discover_sync(include_listed: bool = False) -> list[dict]:
    """
    Discover currently open Indian IPOs.

    Source priority:
      1. ipoalerts.in (IPOALERTS_API_KEY) — free plan supports status=open only.
         Results are cached 24 h so the 25 req/day quota is not wasted.
      2. Google News RSS — zero-cost fallback; results are less reliable.

    Note: upcoming and listed are not available from ipoalerts.in free plan.
    The seed script augments open results with a curated upcoming list.
    """
    api_key = os.getenv("IPOALERTS_API_KEY", "").strip()
    if api_key:
        candidates = _fetch_ipoalerts_sync(api_key, statuses=("open",))
        if candidates:
            return candidates
        logger.warning("ipoalerts.in returned no results — falling back to RSS")

    return _discover_rss()


@router.get("/discover")
async def discover_ipos(include_listed: bool = Query(default=False)):
    """
    Discover current/upcoming Indian IPOs from ipoalerts.in or Google News RSS.
    Pass ?include_listed=true to also include recently listed IPOs.
    Filters out companies already saved in the DB so the list only shows new ones.
    """
    from sqlalchemy import select as sa_select
    loop = asyncio.get_running_loop()
    candidates = await loop.run_in_executor(_executor, _discover_sync, include_listed)

    # Remove candidates that are already in the DB
    async with SessionLocal() as session:
        result = await session.execute(sa_select(IPO.id).where(IPO.id.like("live_%")))
        existing_slugs = {row[0] for row in result.fetchall()}

    fresh = [
        c for c in candidates
        if f"live_{_slug(c['company_name'])}" not in existing_slugs
    ]
    return {"candidates": fresh, "count": len(fresh)}


# ── Batch analyze + save ──────────────────────────────────────────────────────

class BatchAnalyzeRequest(BaseModel):
    companies: list[LiveAnalysisRequest]


class BatchResultItem(BaseModel):
    company_name: str
    ipo_id: str | None = None
    verdict: str | None = None
    confidence_score: float | None = None
    risk_label: str | None = None
    listing_gain_pct: float | None = None
    error: str | None = None


@router.post("/batch", response_model=list[BatchResultItem])
async def batch_analyze(req: BatchAnalyzeRequest):
    """
    Analyze and save multiple IPOs in one call. Each company is analyzed
    using live market data + news and the result is persisted to the DB.
    Max 10 companies per request.
    """
    companies = req.companies[:10]
    results: list[BatchResultItem] = []

    # Fetch market data once — shared across all companies
    market = await _get_market()
    orchestrator = ModelOrchestrator.get()

    # Pre-warm FinBERT in the executor before concurrent calls so the
    # threading lock in _load() is only contested during the warm-up,
    # not by all workers simultaneously on cold start.
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_executor, lambda: orchestrator._finbert()._load())

    async def _analyze_one(company_req: LiveAnalysisRequest) -> BatchResultItem:
        try:
            headlines = await _get_headlines(company_req.company_name, company_req.news_override)
            _loop = asyncio.get_running_loop()
            sentiment_raw = await _loop.run_in_executor(
                _executor,
                lambda: orchestrator.get_sentiment_score(company_req.company_name, texts=headlines),
            )
            features = {
                "sentiment_score":    sentiment_raw["score"],
                "ofs_pct":            company_req.ofs_pct,
                "promoter_stake_pre": company_req.promoter_stake_pre,
                "log_issue_size_cr":  math.log1p(max(company_req.issue_size_cr, 1)),
                "nifty_30d_return":   market["nifty_30d_return"],
                "vix_at_open":        market["vix_current"],
            }
            risk_raw     = orchestrator.predict_risk(features)
            sub_raw      = orchestrator.predict_subscription(features)
            listing_gain = orchestrator.predict_listing_gain(features)

            # ML baseline
            ml_confidence = round(
                0.5 * 50.0 + 0.3 * sentiment_raw["score"] + 0.2 * (100 - risk_raw["risk_score"]), 1
            )
            ml_verdict = (
                "Strong Buy" if ml_confidence >= 75 else
                "Buy"        if ml_confidence >= 60 else
                "Neutral"    if ml_confidence >= 40 else
                "Avoid"
            )

            # DIAL assessment — primary override
            dial = await _loop.run_in_executor(
                _executor,
                assess_ipo_sync,
                company_req.company_name, company_req.sector, headlines,
                risk_raw["risk_score"], sentiment_raw["score"],
                round(float(listing_gain), 1), market,
                company_req.issue_size_cr, company_req.price_band_high,
            )

            if dial:
                confidence       = dial["confidence_score"]
                verdict          = dial["verdict"]
                listing_gain     = dial["listing_gain_pct"]
                dial_risk        = dial["risk_label"]
                risk_raw["risk_label"] = dial_risk
                risk_raw["risk_score"] = {"Low": 22.0, "Medium": 50.0, "High": 76.0}[dial_risk]
                _probs = {"Low": (0.65, 0.25, 0.10), "Medium": (0.20, 0.60, 0.20), "High": (0.05, 0.25, 0.70)}
                risk_raw["prob_low"], risk_raw["prob_medium"], risk_raw["prob_high"] = _probs[dial_risk]
                narrative        = dial.get("reasoning") or None
                inferred_status  = dial.get("status")
            else:
                confidence, verdict = ml_confidence, ml_verdict
                narrative, inferred_status = None, None

            result = LiveAnalysisResponse(
                company_name     = company_req.company_name,
                sector           = company_req.sector,
                sentiment        = SentimentResponse(ipo_id="live", **sentiment_raw),
                risk             = RiskResponse(ipo_id="live", fraud_flags=[], **risk_raw),
                subscription     = SubscriptionResponse(ipo_id="live", **sub_raw),
                listing_gain_pct = round(float(listing_gain), 1),
                confidence_score = confidence,
                verdict          = verdict,
                market_context   = MarketContext(**market),
                news_headlines   = headlines,
            )
            result.ai_narrative = narrative

            ipo_id = await _persist_to_db(company_req, result, headlines, status_override=inferred_status)

            return BatchResultItem(
                company_name     = company_req.company_name,
                ipo_id           = ipo_id,
                verdict          = verdict,
                confidence_score = confidence,
                risk_label       = risk_raw["risk_label"],
                listing_gain_pct = round(float(listing_gain), 1),
            )
        except Exception as e:
            return BatchResultItem(company_name=company_req.company_name, error=str(e))

    # Run all analyses concurrently
    tasks = [_analyze_one(c) for c in companies]
    results = list(await asyncio.gather(*tasks))
    return results
