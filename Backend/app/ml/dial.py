"""Shared EPAM DIAL (GPT-4o proxy) helper functions.

All functions gracefully return None / original input when DIAL credentials
are absent or the API call fails, so every caller has a safe fallback.
"""
import json
import logging
import os
import re

logger = logging.getLogger(__name__)

_SECTORS = [
    "IT Services", "Fintech", "Healthcare", "E-Commerce", "BFSI",
    "Manufacturing", "Consumer", "Renewable Energy", "Insurance",
    "Logistics", "Automobiles", "EdTech", "Agriculture",
]


def _dial_post(prompt: str, max_tokens: int = 200, temperature: float = 0.3) -> str | None:
    """Low-level DIAL call. Returns the assistant message text or None on any failure."""
    api_url = os.getenv("DIAL_API_URL", "").rstrip("/")
    api_key = os.getenv("DIAL_API_KEY", "")
    model   = os.getenv("DIAL_MODEL", "gpt-4o")
    if not (api_url and api_key):
        return None
    try:
        import httpx
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
                "max_tokens":  max_tokens,
                "temperature": temperature,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("DIAL call failed: %s", exc)
        return None


def generate_narrative_sync(
    company_name: str,
    sector: str,
    verdict: str,
    confidence: float,
    risk_label: str,
    sentiment_score: float,
    listing_gain_pct: float,
    market_context: dict,
) -> str | None:
    """Generate a 3-sentence investment narrative for one IPO."""
    prompt = (
        f"You are a SEBI-registered analyst. Write a concise 3-sentence investment "
        f"narrative for {company_name} ({sector} sector) IPO.\n"
        f"AI verdict: {verdict} | Confidence: {confidence:.0f}/100 | "
        f"Risk: {risk_label} | Sentiment: {sentiment_score:.0f}/100 | "
        f"Predicted listing gain: {listing_gain_pct:+.1f}%\n"
        f"Market: Nifty 30D return {market_context.get('nifty_30d_return', 0.0):+.1f}%, "
        f"India VIX {market_context.get('vix_current', 15.0):.1f}\n"
        f"Be specific, data-driven, and mention 1 key risk. No markdown. Plain text only."
    )
    result = _dial_post(prompt, max_tokens=180, temperature=0.3)
    if result:
        logger.info("DIAL narrative OK for %r", company_name)
    return result


def filter_candidates_sync(candidates: list[str]) -> list[str]:
    """
    Filter a raw list of RSS-extracted strings to keep only valid company names.
    Returns the original list unchanged if DIAL is unavailable or the call fails.
    """
    if not candidates:
        return candidates
    prompt = (
        "From the following list, return ONLY valid Indian company names that could "
        "realistically be IPO candidates. Remove sentence fragments, verbs, adjectives, "
        "news phrases, and non-company strings. "
        "Return ONLY a valid JSON array of strings (no explanation, no markdown).\n\n"
        "Input list:\n"
        + json.dumps(candidates)
    )
    raw = _dial_post(prompt, max_tokens=300, temperature=0)
    if not raw:
        return candidates
    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
        filtered = json.loads(raw)
        if isinstance(filtered, list) and filtered:
            logger.info("DIAL candidate filter: %d → %d names", len(candidates), len(filtered))
            return [str(n) for n in filtered]
    except Exception as exc:
        logger.warning("DIAL candidate filter parse failed: %s", exc)
    return candidates


def discover_current_ipos_sync() -> list[dict]:
    """
    Ask DIAL for a list of Indian IPOs that are genuinely open or upcoming
    as of today (April 26, 2026).  Returns structured dicts with price bands
    and dates already filled in.  Returns [] if DIAL is unavailable.
    """
    sectors_str = ", ".join(_SECTORS)
    prompt = (
        "You are an expert on Indian capital markets with up-to-date knowledge of NSE/BSE filings.\n"
        "Today is April 26, 2026.\n\n"
        "List Indian IPOs (mainboard AND SME) that are:\n"
        "  (a) Currently OPEN for subscription (subscription window is active right now), OR\n"
        "  (b) UPCOMING — SEBI-approved and opening within the next 3 weeks.\n\n"
        "IMPORTANT: Do NOT include any IPO that has already LISTED (completed trading debut) on NSE or BSE.\n"
        "Be accurate — only include IPOs you are confident about.\n\n"
        "For each IPO return these fields:\n"
        "  company_name  — official company name\n"
        "  sector        — one of: " + sectors_str + "\n"
        "  issue_size_cr — total issue size in crore INR (number)\n"
        "  price_band_low  — lower price band in INR (number)\n"
        "  price_band_high — upper price band in INR (number)\n"
        "  open_date     — subscription open date YYYY-MM-DD (or null)\n"
        "  close_date    — subscription close date YYYY-MM-DD (or null)\n"
        "  status        — exactly 'open' or 'upcoming'\n\n"
        "Return ONLY a valid JSON array. No markdown, no explanation.\n"
        "Example: [{\"company_name\":\"Acme Ltd\",\"sector\":\"Manufacturing\","
        "\"issue_size_cr\":500,\"price_band_low\":200,\"price_band_high\":210,"
        "\"open_date\":\"2026-04-25\",\"close_date\":\"2026-04-29\",\"status\":\"open\"}]"
    )
    raw = _dial_post(prompt, max_tokens=900, temperature=0.1)
    if not raw:
        return []
    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        valid = []
        for item in data:
            name = str(item.get("company_name") or "").strip()
            if not name:
                continue
            status = str(item.get("status") or "upcoming").lower()
            if status not in ("open", "upcoming"):
                status = "upcoming"
            valid.append({
                "company_name":   name,
                "sector":         str(item.get("sector") or "BFSI"),
                "issue_size_cr":  float(item.get("issue_size_cr") or 500),
                "price_band_low":  float(item.get("price_band_low") or 0),
                "price_band_high": float(item.get("price_band_high") or 0),
                "open_date":       item.get("open_date"),
                "close_date":      item.get("close_date"),
                "status":          status,
                "source":          "dial_discover",
            })
        logger.info("DIAL discover: %d open/upcoming IPOs returned", len(valid))
        return valid
    except Exception as exc:
        logger.warning("DIAL discover parse failed: %s | raw=%.300s", exc, raw)
        return []


def assess_ipo_sync(
    company_name: str,
    sector: str,
    headlines: list[str],
    ml_risk_score: float,
    ml_sentiment_score: float,
    ml_listing_gain: float,
    market: dict,
    issue_size_cr: float = 500.0,
    price_band_high: float = 0.0,
) -> dict | None:
    """
    Primary IPO assessment using DIAL's company knowledge.

    ML model outputs are passed as approximate signals only — the XGBoost risk
    model was trained on 18 features but live inference provides only 6, so its
    risk_score is systematically inflated. DIAL overrides all final outputs.

    Returns dict with keys:
        risk_label, confidence_score, listing_gain_pct, verdict, status, reasoning
    or None if DIAL is unavailable.
    """
    nifty = market.get("nifty_30d_return", 0.0)
    vix   = market.get("vix_current", 15.0)
    market_mood = "bullish" if nifty > 3 else "bearish" if nifty < -3 else "neutral"
    vix_mood = (
        "low volatility — supportive for IPOs" if vix < 15 else
        "elevated volatility — exercise caution" if vix < 25 else
        "high volatility — risk-off environment"
    )
    headlines_text = (
        "\n".join(f"- {h}" for h in headlines[:5])
        if headlines else "No headlines available."
    )
    # Small-cap flag: < ₹300 Cr issue size
    size_context = (
        f"Small-cap IPO (₹{issue_size_cr:.0f} Cr) — limited analyst coverage; "
        f"weight FinBERT sentiment heavily as primary signal."
        if issue_size_cr < 300 else
        f"Mid/Large-cap IPO (₹{issue_size_cr:.0f} Cr) — use your knowledge of the company."
    )

    prompt = (
        f"You are a SEBI-registered IPO analyst with deep knowledge of Indian capital markets. "
        f"Today is April 26, 2026. Assess the {company_name} IPO.\n\n"
        f"Company: {company_name}\n"
        f"Sector: {sector}\n"
        f"Issue size: ₹{issue_size_cr:.0f} Cr | Price band high: ₹{price_band_high:.0f}\n"
        f"{size_context}\n\n"
        f"Recent news headlines:\n{headlines_text}\n\n"
        f"ML model signals (trained on 6 of 17 features — use as hints, not truth):\n"
        f"- FinBERT sentiment: {ml_sentiment_score:.0f}/100  ← most reliable signal\n"
        f"- XGBoost risk score: {ml_risk_score:.0f}/100  ← inflated (zero-filled features); override\n"
        f"- Ridge listing gain: {ml_listing_gain:+.1f}%  ← biased low (missing GMP/subscription); override\n\n"
        f"Market conditions (April 2026):\n"
        f"- Nifty 50 30-day return: {nifty:+.1f}% ({market_mood})\n"
        f"- India VIX: {vix:.1f} ({vix_mood})\n\n"
        f"Indian IPO sector base rates (2019-2024 historical averages for calibration):\n"
        f"- BFSI/Fintech: avg +12%, range -10% to +80%\n"
        f"- Infrastructure/Power/Utilities: avg +8%, range -15% to +40%\n"
        f"- Technology/IT Services: avg +20%, range -5% to +90%\n"
        f"- Healthcare/Pharma: avg +15%, range -10% to +60%\n"
        f"- Consumer/FMCG/Retail: avg +10%, range -20% to +50%\n"
        f"- Manufacturing/Engineering: avg +9%, range -20% to +45%\n"
        f"- SME IPOs: avg +25%, range -30% to +150% (high variance)\n\n"
        f"Using your knowledge of {company_name} (promoters, financials, sector position, "
        f"DRHP/listing timeline), produce a well-calibrated assessment. "
        f"Return ONLY a valid JSON object (no markdown, no explanation):\n"
        f'{{"risk_label":"Low|Medium|High","confidence_score":0-100,'
        f'"listing_gain_pct":number,"verdict":"Strong Buy|Buy|Neutral|Avoid",'
        f'"status":"open|upcoming|listed",'
        f'"reasoning":"2-3 sentences: company strengths, market context, 1 key risk"}}\n\n'
        f"confidence_score thresholds: >=75=Strong Buy, >=60=Buy, >=40=Neutral, <40=Avoid\n"
        f"listing_gain_pct: your own estimate based on sector base rates + sentiment, "
        f"NOT the Ridge signal above.\n"
        f"status: open/upcoming/listed based on April 2026 IPO calendar."
    )
    raw = _dial_post(prompt, max_tokens=320, temperature=0.2)
    if not raw:
        return None
    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip("`").strip()
        data = json.loads(raw)

        risk_label = data.get("risk_label", "Medium")
        if risk_label not in ("Low", "Medium", "High"):
            risk_label = "Medium"

        confidence = float(data.get("confidence_score", 50))
        confidence = max(0.0, min(100.0, confidence))

        listing_gain = float(data.get("listing_gain_pct", 0.0))
        listing_gain = max(-50.0, min(200.0, listing_gain))

        verdict = data.get("verdict", "Neutral")
        if verdict not in ("Strong Buy", "Buy", "Neutral", "Avoid"):
            verdict = (
                "Strong Buy" if confidence >= 75 else
                "Buy"        if confidence >= 60 else
                "Neutral"    if confidence >= 40 else
                "Avoid"
            )

        status = data.get("status", "upcoming")
        if status not in ("open", "upcoming", "listed"):
            status = "upcoming"

        reasoning = str(data.get("reasoning", "")).strip()
        logger.info(
            "DIAL assess %r → risk=%s conf=%.0f gain=%+.1f%% verdict=%s status=%s",
            company_name, risk_label, confidence, listing_gain, verdict, status,
        )
        return {
            "risk_label":       risk_label,
            "confidence_score": confidence,
            "listing_gain_pct": listing_gain,
            "verdict":          verdict,
            "status":           status,
            "reasoning":        reasoning,
        }
    except Exception as exc:
        logger.warning("DIAL assess parse failed for %r: %s | raw=%.200s", company_name, exc, raw)
        return None


def generate_insights_sync(stats: dict, market: dict) -> str:
    """
    Generate a 2-sentence AI market summary from dashboard stats + market data.
    Returns a fallback string if DIAL is unavailable.
    """
    top_ipos = ", ".join(
        f"{ipo['company_name']} ({ipo.get('verdict', 'N/A')})"
        for ipo in (stats.get("top_ipos") or [])[:3]
    ) or "N/A"

    prompt = (
        f"You are a financial analyst summarizing the current Indian IPO market. "
        f"Write exactly 2 sentences (no bullet points, no markdown, plain text only) "
        f"covering the key trends and an investor takeaway.\n\n"
        f"Dashboard data:\n"
        f"- Open IPOs: {stats.get('open_ipos', 0)} | Upcoming: {stats.get('upcoming_ipos', 0)} | "
        f"Listed: {stats.get('listed_ipos', 0)}\n"
        f"- Avg financial score: {stats.get('avg_financial_score', 50):.0f}/100 | "
        f"Avg sentiment: {stats.get('avg_sentiment_score', 50):.0f}/100\n"
        f"- Risk distribution — High: {stats.get('high_risk_count', 0)}, "
        f"Medium: {stats.get('medium_risk_count', 0)}, Low: {stats.get('low_risk_count', 0)}\n"
        f"- Strong Buy count: {stats.get('strong_buy_count', 0)}\n"
        f"- Top IPOs by confidence: {top_ipos}\n"
        f"- Nifty 30D return: {market.get('nifty_30d_return', 0.0):+.1f}% | "
        f"India VIX: {market.get('vix_current', 15.0):.1f}"
    )
    result = _dial_post(prompt, max_tokens=120, temperature=0.4)
    if result:
        logger.info("DIAL insights generated successfully")
        return result
    # Fallback: data-driven static text
    open_count = stats.get("open_ipos", 0)
    sentiment  = stats.get("avg_sentiment_score", 50)
    mood = "positive" if sentiment >= 60 else "cautious" if sentiment >= 40 else "bearish"
    return (
        f"There are currently {open_count} open IPO(s) with overall market sentiment "
        f"appearing {mood} (avg score {sentiment:.0f}/100). "
        f"Nifty 50 has moved {market.get('nifty_30d_return', 0.0):+.1f}% over the last 30 days "
        f"with India VIX at {market.get('vix_current', 15.0):.1f}."
    )
