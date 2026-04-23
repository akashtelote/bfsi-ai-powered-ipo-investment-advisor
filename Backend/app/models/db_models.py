from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class IPO(Base):
    __tablename__ = "ipos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(100))
    issue_size_cr: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_band_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_band_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    close_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    listing_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")  # open/upcoming/listed
    listing_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    listing_gain_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    gmp_t3: Mapped[float | None] = mapped_column(Float, nullable=True)
    promoter_stake_pre: Mapped[float | None] = mapped_column(Float, nullable=True)
    ofs_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    fresh_issue_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Scores (populated after ML inference)
    financial_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_label: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_sub_multiple: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FinancialScore(Base):
    __tablename__ = "financial_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ipo_id: Mapped[str] = mapped_column(String, index=True)
    profitability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    solvency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    efficiency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ipo_id: Mapped[str] = mapped_column(String, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    label: Mapped[str | None] = mapped_column(String(20), nullable=True)  # positive/neutral/negative
    positive_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    neutral_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    negative_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    news_volume_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ipo_id: Mapped[str] = mapped_column(String, index=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_label: Mapped[str | None] = mapped_column(String(10), nullable=True)
    prob_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_medium: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    shap_top_drivers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    fraud_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)


class PeerData(Base):
    __tablename__ = "peer_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ipo_id: Mapped[str] = mapped_column(String, index=True)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    peers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    peer_pe_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    peer_ev_ebitda_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    ipo_pe: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_label: Mapped[str | None] = mapped_column(String(20), nullable=True)


class SubscriptionForecast(Base):
    __tablename__ = "subscription_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ipo_id: Mapped[str] = mapped_column(String, index=True)
    qib_predicted: Mapped[float | None] = mapped_column(Float, nullable=True)
    hni_predicted: Mapped[float | None] = mapped_column(Float, nullable=True)
    rii_predicted: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_predicted: Mapped[float | None] = mapped_column(Float, nullable=True)
    allotment_probability: Mapped[float | None] = mapped_column(Float, nullable=True)


class InvestorProfile(Base):
    __tablename__ = "investor_profiles"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    risk_tolerance: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    preferred_sectors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    investment_horizon: Mapped[str] = mapped_column(String(20), default="medium")  # short/medium/long
    portfolio_size: Mapped[str] = mapped_column(String(20), default="medium")
    sebi_category: Mapped[str] = mapped_column(String(10), default="RII")  # RII/HNI/QIB
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
