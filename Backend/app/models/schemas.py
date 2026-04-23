from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── IPO List / Summary ───────────────────────────────────────────────────────

class IPOSummary(BaseModel):
    id: str
    company_name: str
    sector: str
    status: str
    issue_size_cr: Optional[float] = None
    price_band_low: Optional[float] = None
    price_band_high: Optional[float] = None
    open_date: Optional[str] = None
    close_date: Optional[str] = None
    listing_date: Optional[str] = None
    financial_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    risk_score: Optional[float] = None
    risk_label: Optional[str] = None
    confidence_score: Optional[float] = None
    valuation_label: Optional[str] = None
    overall_sub_multiple: Optional[float] = None

    class Config:
        from_attributes = True


class IPOListResponse(BaseModel):
    items: list[IPOSummary]
    total: int
    page: int
    page_size: int


# ─── Financial Scores ─────────────────────────────────────────────────────────

class FinancialPillars(BaseModel):
    profitability: float
    growth: float
    liquidity: float
    solvency: float
    efficiency: float
    overall: float


class FinancialScoreResponse(BaseModel):
    ipo_id: str
    pillars: FinancialPillars
    raw_features: Optional[dict] = None


# ─── Sentiment ────────────────────────────────────────────────────────────────

class SentimentResponse(BaseModel):
    ipo_id: str
    score: float
    label: str
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    top_keywords: list[str]
    news_volume_7d: int


# ─── Risk ─────────────────────────────────────────────────────────────────────

class SHAPDriver(BaseModel):
    feature: str
    value: float
    direction: str  # "increases_risk" | "decreases_risk"
    display_name: str


class FraudFlag(BaseModel):
    rule_id: str
    severity: str  # "high" | "medium" | "low"
    description: str


class RiskResponse(BaseModel):
    ipo_id: str
    risk_score: float
    risk_label: str
    prob_low: float
    prob_medium: float
    prob_high: float
    shap_top_drivers: list[SHAPDriver]
    fraud_flags: list[FraudFlag]


# ─── Peers ────────────────────────────────────────────────────────────────────

class PeerCompany(BaseModel):
    ticker: str
    name: str
    pe: Optional[float] = None
    ev_ebitda: Optional[float] = None
    market_cap_cr: Optional[float] = None


class PeersResponse(BaseModel):
    ipo_id: str
    ipo_pe: Optional[float] = None
    peer_pe_median: Optional[float] = None
    peer_ev_ebitda_median: Optional[float] = None
    valuation_label: str
    peers: list[PeerCompany]


# ─── Subscription ─────────────────────────────────────────────────────────────

class SubscriptionResponse(BaseModel):
    ipo_id: str
    qib_predicted: float
    hni_predicted: float
    rii_predicted: float
    overall_predicted: float
    allotment_probability: float
    capital_needed_rii: Optional[float] = None


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_ipos: int
    open_ipos: int
    upcoming_ipos: int
    listed_ipos: int
    avg_financial_score: float
    avg_sentiment_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    strong_buy_count: int
    top_ipos: list[IPOSummary]


# ─── Recommendations ──────────────────────────────────────────────────────────

class RecommendationItem(BaseModel):
    ipo: IPOSummary
    suitability_score: float
    verdict: str  # "Strong Buy" | "Buy" | "Neutral" | "Avoid"
    reasons: list[str]


class RecommendationRequest(BaseModel):
    user_id: str
    risk_tolerance: int = Field(default=3, ge=1, le=5)
    preferred_sectors: list[str] = []
    investment_horizon: str = "medium"
    portfolio_size: str = "medium"
    sebi_category: str = "RII"


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[RecommendationItem]
    generated_at: str


# ─── Full IPO Detail ──────────────────────────────────────────────────────────

class IPODetail(BaseModel):
    ipo: IPOSummary
    financial: Optional[FinancialScoreResponse] = None
    sentiment: Optional[SentimentResponse] = None
    risk: Optional[RiskResponse] = None
    peers: Optional[PeersResponse] = None
    subscription: Optional[SubscriptionResponse] = None
    verdict: Optional[str] = None  # "Strong Buy" | "Buy" | "Neutral" | "Avoid"


# ─── Investor Profile ─────────────────────────────────────────────────────────

class InvestorProfileRequest(BaseModel):
    user_id: str
    risk_tolerance: int = Field(default=3, ge=1, le=5)
    preferred_sectors: list[str] = []
    investment_horizon: str = "medium"
    portfolio_size: str = "medium"
    sebi_category: str = "RII"


class InvestorProfileResponse(BaseModel):
    user_id: str
    risk_tolerance: int
    preferred_sectors: list[str]
    investment_horizon: str
    portfolio_size: str
    sebi_category: str

    class Config:
        from_attributes = True


# ─── Compare ──────────────────────────────────────────────────────────────────

class CompareResponse(BaseModel):
    ipos: list[IPODetail]


# ─── Live Analysis ────────────────────────────────────────────────────────────

class MarketContext(BaseModel):
    nifty_30d_return: float
    vix_current: float
    fetched_at: str                  # ISO UTC datetime string


class LiveAnalysisRequest(BaseModel):
    company_name: str
    sector: str
    issue_size_cr: float
    ofs_pct: float = 0.0
    promoter_stake_pre: float = 0.0
    price_band_low: float
    price_band_high: float
    news_override: Optional[list[str]] = None   # bypasses RSS fetch


class LiveAnalysisResponse(BaseModel):
    company_name: str
    sector: str
    sentiment: SentimentResponse
    risk: RiskResponse
    subscription: SubscriptionResponse
    listing_gain_pct: float
    confidence_score: float
    verdict: str
    market_context: MarketContext
    news_headlines: list[str]
