"""
seed_db.py — Populates the SQLite database with demo IPO data.
If ipo_master.csv exists, reads from it; otherwise inserts 20 curated demo IPOs.
Usage: python backend/data/seed_db.py   (from repo root)
       python seed_db.py                 (from backend/data/)
"""
import asyncio
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import init_db, SessionLocal
from app.models.db_models import (
    IPO, FinancialScore, SentimentScore, RiskScore, PeerData, SubscriptionForecast
)

MASTER_CSV = os.path.join(os.path.dirname(__file__), "ipo_master.csv")
SENTIMENT_CSV = os.path.join(os.path.dirname(__file__), "sentiment_scores.csv")


# ─── 20 Curated Demo IPOs ─────────────────────────────────────────────────────
# Each entry has: ipo (IPO table), _financial, _sentiment, _risk, _peers, _subscription

DEMO_DATA = [
    # ── 1. Tata Technologies ──────────────────────────────────────────────────
    {
        "ipo": {
            "id": "tata_tech_2023", "company_name": "Tata Technologies", "sector": "IT Services",
            "status": "listed", "issue_size_cr": 3042, "price_band_low": 475, "price_band_high": 500,
            "listing_date": "2023-11-30", "listing_gain_pct": 140.3, "promoter_stake_pre": 55.6,
            "ofs_pct": 100.0, "fresh_issue_pct": 0.0,
            "financial_score": 88, "sentiment_score": 85, "risk_score": 18,
            "risk_label": "Low", "confidence_score": 88, "valuation_label": "Fair",
            "overall_sub_multiple": 69.4,
        },
        "_financial": {"profitability_score": 90, "growth_score": 86, "liquidity_score": 88,
                       "solvency_score": 92, "efficiency_score": 84},
        "_sentiment": {"score": 85, "label": "positive", "positive_pct": 72, "neutral_pct": 20,
                       "negative_pct": 8, "top_keywords": ["tata", "engineering", "ev", "global", "growth"],
                       "news_volume_7d": 142},
        "_risk": {
            "risk_score": 18, "risk_label": "Low", "prob_low": 0.78, "prob_medium": 0.18, "prob_high": 0.04,
            "shap_top_drivers": [
                {"feature": "roce", "value": 2.8, "direction": "decreases_risk", "display_name": "High ROCE"},
                {"feature": "revenue_growth_yoy", "value": 2.1, "direction": "decreases_risk", "display_name": "Revenue Growth YoY"},
                {"feature": "net_profit_margin", "value": 1.9, "direction": "decreases_risk", "display_name": "Net Profit Margin"},
                {"feature": "promoter_stake_pre", "value": 1.4, "direction": "decreases_risk", "display_name": "Promoter Stake"},
                {"feature": "ofs_pct", "value": -0.9, "direction": "increases_risk", "display_name": "OFS % (full exit)"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 28.5, "peer_pe_median": 26.2, "peer_ev_ebitda_median": 18.4,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "INFY", "name": "Infosys", "pe": 27.8, "ev_ebitda": 17.2, "market_cap_cr": 620000},
                {"ticker": "WIPRO", "name": "Wipro", "pe": 21.3, "ev_ebitda": 14.8, "market_cap_cr": 245000},
                {"ticker": "LTIM", "name": "LTIMindtree", "pe": 31.4, "ev_ebitda": 20.1, "market_cap_cr": 135000},
                {"ticker": "KPIT", "name": "KPIT Technologies", "pe": 42.6, "ev_ebitda": 28.3, "market_cap_cr": 35000},
            ],
        },
        "_subscription": {"qib_predicted": 203.4, "hni_predicted": 62.1, "rii_predicted": 25.3,
                          "overall_predicted": 69.4, "allotment_probability": 0.08},
    },
    # ── 2. Hyundai India ──────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "hyundai_india_2024", "company_name": "Hyundai Motor India", "sector": "Automobiles",
            "status": "listed", "issue_size_cr": 27870, "price_band_low": 1865, "price_band_high": 1960,
            "listing_date": "2024-10-22", "listing_gain_pct": -1.3, "promoter_stake_pre": 100.0,
            "ofs_pct": 100.0, "fresh_issue_pct": 0.0,
            "financial_score": 82, "sentiment_score": 68, "risk_score": 28,
            "risk_label": "Low", "confidence_score": 78, "valuation_label": "Fair",
            "overall_sub_multiple": 2.4,
        },
        "_financial": {"profitability_score": 85, "growth_score": 76, "liquidity_score": 80,
                       "solvency_score": 88, "efficiency_score": 82},
        "_sentiment": {"score": 68, "label": "neutral", "positive_pct": 48, "neutral_pct": 36,
                       "negative_pct": 16, "top_keywords": ["hyundai", "suv", "maruti", "ev", "valuation"],
                       "news_volume_7d": 210},
        "_risk": {
            "risk_score": 28, "risk_label": "Low", "prob_low": 0.65, "prob_medium": 0.29, "prob_high": 0.06,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": 2.2, "direction": "decreases_risk", "display_name": "Net Profit Margin"},
                {"feature": "roce", "value": 1.8, "direction": "decreases_risk", "display_name": "ROCE"},
                {"feature": "ofs_pct", "value": -1.6, "direction": "increases_risk", "display_name": "100% OFS (promoter exit)"},
                {"feature": "revenue_growth_yoy", "value": 1.1, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "debt_equity_ratio", "value": -0.6, "direction": "increases_risk", "display_name": "Debt-Equity Ratio"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 26.3, "peer_pe_median": 24.1, "peer_ev_ebitda_median": 14.6,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "MARUTI", "name": "Maruti Suzuki", "pe": 28.4, "ev_ebitda": 16.2, "market_cap_cr": 385000},
                {"ticker": "M&M", "name": "Mahindra & Mahindra", "pe": 22.1, "ev_ebitda": 13.8, "market_cap_cr": 290000},
                {"ticker": "TATAMOTORS", "name": "Tata Motors", "pe": 12.3, "ev_ebitda": 7.4, "market_cap_cr": 240000},
            ],
        },
        "_subscription": {"qib_predicted": 4.8, "hni_predicted": 1.9, "rii_predicted": 0.5,
                          "overall_predicted": 2.4, "allotment_probability": 0.72},
    },
    # ── 3. Bajaj Housing Finance ──────────────────────────────────────────────
    {
        "ipo": {
            "id": "bajaj_housing_2024", "company_name": "Bajaj Housing Finance", "sector": "BFSI",
            "status": "listed", "issue_size_cr": 6560, "price_band_low": 66, "price_band_high": 70,
            "listing_date": "2024-09-16", "listing_gain_pct": 114.0, "promoter_stake_pre": 100.0,
            "ofs_pct": 0.0, "fresh_issue_pct": 100.0,
            "financial_score": 86, "sentiment_score": 80, "risk_score": 22,
            "risk_label": "Low", "confidence_score": 84, "valuation_label": "Fair",
            "overall_sub_multiple": 63.6,
        },
        "_financial": {"profitability_score": 88, "growth_score": 90, "liquidity_score": 82,
                       "solvency_score": 84, "efficiency_score": 86},
        "_sentiment": {"score": 80, "label": "positive", "positive_pct": 66, "neutral_pct": 25,
                       "negative_pct": 9, "top_keywords": ["bajaj", "housing", "nbfc", "growth", "npa"],
                       "news_volume_7d": 118},
        "_risk": {
            "risk_score": 22, "risk_label": "Low", "prob_low": 0.72, "prob_medium": 0.23, "prob_high": 0.05,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 2.6, "direction": "decreases_risk", "display_name": "Loan Book Growth"},
                {"feature": "net_profit_margin", "value": 2.0, "direction": "decreases_risk", "display_name": "Net Interest Margin"},
                {"feature": "promoter_stake_pre", "value": 1.6, "direction": "decreases_risk", "display_name": "Promoter Commitment"},
                {"feature": "fresh_issue_pct", "value": 1.2, "direction": "decreases_risk", "display_name": "Fresh Issue (capital infusion)"},
                {"feature": "debt_equity_ratio", "value": -1.1, "direction": "increases_risk", "display_name": "Debt-Equity (NBFC leverage)"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 32.4, "peer_pe_median": 28.6, "peer_ev_ebitda_median": 22.1,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "HDFCBANK", "name": "HDFC Bank", "pe": 18.4, "ev_ebitda": 14.2, "market_cap_cr": 1240000},
                {"ticker": "BAJFINANCE", "name": "Bajaj Finance", "pe": 34.2, "ev_ebitda": 26.8, "market_cap_cr": 420000},
                {"ticker": "LTFH", "name": "L&T Finance", "pe": 14.6, "ev_ebitda": 11.3, "market_cap_cr": 38000},
            ],
        },
        "_subscription": {"qib_predicted": 209.4, "hni_predicted": 41.5, "rii_predicted": 7.5,
                          "overall_predicted": 63.6, "allotment_probability": 0.06},
    },
    # ── 4. Zomato ─────────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "zomato_2021", "company_name": "Zomato Ltd", "sector": "Food & Delivery",
            "status": "listed", "issue_size_cr": 9375, "price_band_low": 72, "price_band_high": 76,
            "listing_date": "2021-07-23", "listing_gain_pct": 53.1, "promoter_stake_pre": 15.0,
            "ofs_pct": 20.0, "fresh_issue_pct": 80.0,
            "financial_score": 72, "sentiment_score": 78, "risk_score": 32,
            "risk_label": "Low", "confidence_score": 76, "valuation_label": "Expensive",
            "overall_sub_multiple": 38.2,
        },
        "_financial": {"profitability_score": 58, "growth_score": 88, "liquidity_score": 78,
                       "solvency_score": 72, "efficiency_score": 64},
        "_sentiment": {"score": 78, "label": "positive", "positive_pct": 62, "neutral_pct": 28,
                       "negative_pct": 10, "top_keywords": ["zomato", "delivery", "growth", "losses", "market"],
                       "news_volume_7d": 356},
        "_risk": {
            "risk_score": 32, "risk_label": "Low", "prob_low": 0.60, "prob_medium": 0.32, "prob_high": 0.08,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 2.8, "direction": "decreases_risk", "display_name": "Revenue Growth YoY"},
                {"feature": "gmp_premium", "value": 1.4, "direction": "decreases_risk", "display_name": "GMP Premium"},
                {"feature": "net_profit_margin", "value": -1.8, "direction": "increases_risk", "display_name": "Net Loss (pre-profitability)"},
                {"feature": "cash_conversion_cycle", "value": -1.2, "direction": "increases_risk", "display_name": "Cash Burn Rate"},
                {"feature": "fresh_issue_pct", "value": 1.0, "direction": "decreases_risk", "display_name": "Fresh Capital Raised"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 45.2, "peer_ev_ebitda_median": 30.4,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "JUBLFOOD", "name": "Jubilant FoodWorks", "pe": 48.3, "ev_ebitda": 32.1, "market_cap_cr": 38000},
                {"ticker": "DEVYANI", "name": "Devyani International", "pe": 62.4, "ev_ebitda": 28.6, "market_cap_cr": 22000},
                {"ticker": "WESTLIFE", "name": "Westlife FoodWorld", "pe": 38.1, "ev_ebitda": 22.4, "market_cap_cr": 9800},
            ],
        },
        "_subscription": {"qib_predicted": 51.8, "hni_predicted": 32.2, "rii_predicted": 7.5,
                          "overall_predicted": 38.2, "allotment_probability": 0.12},
    },
    # ── 5. Nykaa ──────────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "nykaa_2021", "company_name": "FSN E-Commerce Ventures (Nykaa)", "sector": "E-Commerce",
            "status": "listed", "issue_size_cr": 5351, "price_band_low": 1085, "price_band_high": 1125,
            "listing_date": "2021-11-10", "listing_gain_pct": 79.4, "promoter_stake_pre": 54.2,
            "ofs_pct": 30.0, "fresh_issue_pct": 70.0,
            "financial_score": 66, "sentiment_score": 80, "risk_score": 42,
            "risk_label": "Medium", "confidence_score": 72, "valuation_label": "Expensive",
            "overall_sub_multiple": 82.0,
        },
        "_financial": {"profitability_score": 55, "growth_score": 82, "liquidity_score": 68,
                       "solvency_score": 64, "efficiency_score": 62},
        "_sentiment": {"score": 80, "label": "positive", "positive_pct": 68, "neutral_pct": 22,
                       "negative_pct": 10, "top_keywords": ["nykaa", "beauty", "omnichannel", "d2c", "profitable"],
                       "news_volume_7d": 228},
        "_risk": {
            "risk_score": 42, "risk_label": "Medium", "prob_low": 0.38, "prob_medium": 0.45, "prob_high": 0.17,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 2.2, "direction": "decreases_risk", "display_name": "Revenue Growth YoY"},
                {"feature": "gmp_premium", "value": 1.6, "direction": "decreases_risk", "display_name": "GMP Premium"},
                {"feature": "valuation_premium", "value": -1.9, "direction": "increases_risk", "display_name": "High Valuation Premium"},
                {"feature": "net_profit_margin", "value": -0.8, "direction": "increases_risk", "display_name": "Thin Profit Margin"},
                {"feature": "promoter_stake_pre", "value": 0.9, "direction": "decreases_risk", "display_name": "Promoter Stake"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 840.0, "peer_pe_median": 62.4, "peer_ev_ebitda_median": 38.2,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "SHOPERSTOP", "name": "Shoppers Stop", "pe": 58.2, "ev_ebitda": 22.4, "market_cap_cr": 9200},
                {"ticker": "TRENT", "name": "Trent Ltd", "pe": 112.4, "ev_ebitda": 62.1, "market_cap_cr": 165000},
                {"ticker": "ABFRL", "name": "Aditya Birla Fashion", "pe": None, "ev_ebitda": 18.6, "market_cap_cr": 18000},
            ],
        },
        "_subscription": {"qib_predicted": 122.4, "hni_predicted": 112.3, "rii_predicted": 12.2,
                          "overall_predicted": 82.0, "allotment_probability": 0.07},
    },
    # ── 6. LIC ────────────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "lic_2022", "company_name": "Life Insurance Corporation", "sector": "Insurance",
            "status": "listed", "issue_size_cr": 21000, "price_band_low": 902, "price_band_high": 949,
            "listing_date": "2022-05-17", "listing_gain_pct": -8.1, "promoter_stake_pre": 100.0,
            "ofs_pct": 100.0, "fresh_issue_pct": 0.0,
            "financial_score": 85, "sentiment_score": 55, "risk_score": 48,
            "risk_label": "Medium", "confidence_score": 62, "valuation_label": "Fair",
            "overall_sub_multiple": 2.95,
        },
        "_financial": {"profitability_score": 88, "growth_score": 72, "liquidity_score": 90,
                       "solvency_score": 86, "efficiency_score": 80},
        "_sentiment": {"score": 55, "label": "neutral", "positive_pct": 38, "neutral_pct": 42,
                       "negative_pct": 20, "top_keywords": ["lic", "government", "insurance", "valuation", "embedded_value"],
                       "news_volume_7d": 480},
        "_risk": {
            "risk_score": 48, "risk_label": "Medium", "prob_low": 0.28, "prob_medium": 0.52, "prob_high": 0.20,
            "shap_top_drivers": [
                {"feature": "ofs_pct", "value": -2.1, "direction": "increases_risk", "display_name": "100% OFS (govt divestment)"},
                {"feature": "valuation_premium", "value": -1.4, "direction": "increases_risk", "display_name": "EV-based Valuation Premium"},
                {"feature": "net_profit_margin", "value": 1.8, "direction": "decreases_risk", "display_name": "Profitability"},
                {"feature": "market_cap", "value": -1.0, "direction": "increases_risk", "display_name": "Large Float Overhang"},
                {"feature": "brand_strength", "value": 1.6, "direction": "decreases_risk", "display_name": "Brand Monopoly"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 14.8, "peer_pe_median": 22.6, "peer_ev_ebitda_median": 16.4,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "HDFCLIFE", "name": "HDFC Life Insurance", "pe": 88.4, "ev_ebitda": None, "market_cap_cr": 148000},
                {"ticker": "SBILIFE", "name": "SBI Life Insurance", "pe": 72.3, "ev_ebitda": None, "market_cap_cr": 155000},
                {"ticker": "ICICIPRU", "name": "ICICI Prudential Life", "pe": 58.1, "ev_ebitda": None, "market_cap_cr": 88000},
            ],
        },
        "_subscription": {"qib_predicted": 2.83, "hni_predicted": 2.35, "rii_predicted": 1.99,
                          "overall_predicted": 2.95, "allotment_probability": 0.62},
    },
    # ── 7. PolicyBazaar ───────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "policybazaar_2021", "company_name": "PB Fintech (PolicyBazaar)", "sector": "Insurance Tech",
            "status": "listed", "issue_size_cr": 5625, "price_band_low": 940, "price_band_high": 980,
            "listing_date": "2021-11-15", "listing_gain_pct": 17.4, "promoter_stake_pre": 25.2,
            "ofs_pct": 35.0, "fresh_issue_pct": 65.0,
            "financial_score": 55, "sentiment_score": 72, "risk_score": 52,
            "risk_label": "Medium", "confidence_score": 60, "valuation_label": "Expensive",
            "overall_sub_multiple": 16.6,
        },
        "_financial": {"profitability_score": 38, "growth_score": 82, "liquidity_score": 60,
                       "solvency_score": 55, "efficiency_score": 50},
        "_sentiment": {"score": 72, "label": "positive", "positive_pct": 56, "neutral_pct": 30,
                       "negative_pct": 14, "top_keywords": ["policybazaar", "insurtech", "digital", "losses", "growth"],
                       "news_volume_7d": 165},
        "_risk": {
            "risk_score": 52, "risk_label": "Medium", "prob_low": 0.22, "prob_medium": 0.50, "prob_high": 0.28,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": -2.4, "direction": "increases_risk", "display_name": "Operating Losses"},
                {"feature": "revenue_growth_yoy", "value": 1.8, "direction": "decreases_risk", "display_name": "Premium Growth YoY"},
                {"feature": "cash_conversion_cycle", "value": -1.2, "direction": "increases_risk", "display_name": "Cash Burn"},
                {"feature": "gmp_premium", "value": 0.8, "direction": "decreases_risk", "display_name": "GMP Positive"},
                {"feature": "promoter_stake_pre", "value": -0.6, "direction": "increases_risk", "display_name": "Low Promoter Stake"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 68.4, "peer_ev_ebitda_median": 42.2,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "HDFCLIFE", "name": "HDFC Life", "pe": 88.4, "ev_ebitda": None, "market_cap_cr": 148000},
                {"ticker": "NUVAMA", "name": "Nuvama Wealth", "pe": 32.1, "ev_ebitda": 22.4, "market_cap_cr": 18000},
            ],
        },
        "_subscription": {"qib_predicted": 22.4, "hni_predicted": 18.9, "rii_predicted": 3.6,
                          "overall_predicted": 16.6, "allotment_probability": 0.28},
    },
    # ── 8. Delhivery ──────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "delhivery_2022", "company_name": "Delhivery Ltd", "sector": "Logistics",
            "status": "listed", "issue_size_cr": 5235, "price_band_low": 462, "price_band_high": 487,
            "listing_date": "2022-05-24", "listing_gain_pct": 1.2, "promoter_stake_pre": 20.4,
            "ofs_pct": 28.0, "fresh_issue_pct": 72.0,
            "financial_score": 58, "sentiment_score": 60, "risk_score": 55,
            "risk_label": "Medium", "confidence_score": 55, "valuation_label": "Fair",
            "overall_sub_multiple": 1.63,
        },
        "_financial": {"profitability_score": 40, "growth_score": 72, "liquidity_score": 62,
                       "solvency_score": 58, "efficiency_score": 58},
        "_sentiment": {"score": 60, "label": "neutral", "positive_pct": 42, "neutral_pct": 40,
                       "negative_pct": 18, "top_keywords": ["delhivery", "logistics", "ecommerce", "supply_chain", "losses"],
                       "news_volume_7d": 88},
        "_risk": {
            "risk_score": 55, "risk_label": "Medium", "prob_low": 0.20, "prob_medium": 0.48, "prob_high": 0.32,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": -2.2, "direction": "increases_risk", "display_name": "Net Losses"},
                {"feature": "revenue_growth_yoy", "value": 1.6, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "cash_conversion_cycle", "value": -1.4, "direction": "increases_risk", "display_name": "Working Capital Needs"},
                {"feature": "promoter_stake_pre", "value": -1.0, "direction": "increases_risk", "display_name": "Low Promoter Stake"},
                {"feature": "fresh_issue_pct", "value": 0.8, "direction": "decreases_risk", "display_name": "Fresh Capital Raised"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 32.4, "peer_ev_ebitda_median": 18.6,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "BLUEDART", "name": "Blue Dart Express", "pe": 52.4, "ev_ebitda": 28.2, "market_cap_cr": 22000},
                {"ticker": "GATI", "name": "Gati Ltd", "pe": 28.6, "ev_ebitda": 14.8, "market_cap_cr": 3800},
                {"ticker": "MAHLOG", "name": "Mahindra Logistics", "pe": 18.4, "ev_ebitda": 12.6, "market_cap_cr": 2900},
            ],
        },
        "_subscription": {"qib_predicted": 2.82, "hni_predicted": 1.58, "rii_predicted": 0.40,
                          "overall_predicted": 1.63, "allotment_probability": 0.80},
    },
    # ── 9. Ola Electric ───────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "ola_electric_2024", "company_name": "Ola Electric Mobility", "sector": "Electric Vehicles",
            "status": "listed", "issue_size_cr": 6145, "price_band_low": 72, "price_band_high": 76,
            "listing_date": "2024-08-09", "listing_gain_pct": 20.2, "promoter_stake_pre": 37.0,
            "ofs_pct": 0.0, "fresh_issue_pct": 100.0,
            "financial_score": 48, "sentiment_score": 82, "risk_score": 68,
            "risk_label": "High", "confidence_score": 55, "valuation_label": "Expensive",
            "overall_sub_multiple": 4.3,
        },
        "_financial": {"profitability_score": 22, "growth_score": 88, "liquidity_score": 42,
                       "solvency_score": 38, "efficiency_score": 50},
        "_sentiment": {"score": 82, "label": "positive", "positive_pct": 70, "neutral_pct": 20,
                       "negative_pct": 10, "top_keywords": ["ola", "electric", "ev", "scooter", "bhavish"],
                       "news_volume_7d": 312},
        "_risk": {
            "risk_score": 68, "risk_label": "High", "prob_low": 0.10, "prob_medium": 0.28, "prob_high": 0.62,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": -3.2, "direction": "increases_risk", "display_name": "Deep Losses"},
                {"feature": "debt_equity_ratio", "value": -2.1, "direction": "increases_risk", "display_name": "High Leverage"},
                {"feature": "cash_conversion_cycle", "value": -1.8, "direction": "increases_risk", "display_name": "Cash Burn Rate"},
                {"feature": "revenue_growth_yoy", "value": 2.4, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "gmp_premium", "value": 1.0, "direction": "decreases_risk", "display_name": "Positive GMP"},
            ],
            "fraud_flags": [
                {"rule_id": "FR001", "severity": "medium", "description": "Operating losses for 3+ consecutive years"},
                {"rule_id": "FR004", "severity": "low", "description": "Related-party transactions with promoter entities exceed 15% of revenues"},
            ],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 28.4, "peer_ev_ebitda_median": 18.6,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "TATAMOTORS", "name": "Tata Motors (EV)", "pe": 12.3, "ev_ebitda": 7.4, "market_cap_cr": 240000},
                {"ticker": "BAJAJ-AUTO", "name": "Bajaj Auto", "pe": 28.4, "ev_ebitda": 22.1, "market_cap_cr": 280000},
                {"ticker": "HEROMOTOCO", "name": "Hero MotoCorp", "pe": 22.6, "ev_ebitda": 14.8, "market_cap_cr": 72000},
            ],
        },
        "_subscription": {"qib_predicted": 8.2, "hni_predicted": 3.9, "rii_predicted": 1.1,
                          "overall_predicted": 4.3, "allotment_probability": 0.52},
    },
    # ── 10. Paytm ─────────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "paytm_2021", "company_name": "One97 Communications (Paytm)", "sector": "Fintech",
            "status": "listed", "issue_size_cr": 18300, "price_band_low": 2080, "price_band_high": 2150,
            "listing_date": "2021-11-18", "listing_gain_pct": -27.3, "promoter_stake_pre": 18.5,
            "ofs_pct": 60.0, "fresh_issue_pct": 40.0,
            "financial_score": 35, "sentiment_score": 60, "risk_score": 78,
            "risk_label": "High", "confidence_score": 38, "valuation_label": "Expensive",
            "overall_sub_multiple": 1.89,
        },
        "_financial": {"profitability_score": 15, "growth_score": 62, "liquidity_score": 38,
                       "solvency_score": 28, "efficiency_score": 32},
        "_sentiment": {"score": 60, "label": "neutral", "positive_pct": 42, "neutral_pct": 36,
                       "negative_pct": 22, "top_keywords": ["paytm", "fintech", "losses", "rbi", "wallet"],
                       "news_volume_7d": 428},
        "_risk": {
            "risk_score": 78, "risk_label": "High", "prob_low": 0.05, "prob_medium": 0.18, "prob_high": 0.77,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": -3.8, "direction": "increases_risk", "display_name": "Persistent Losses"},
                {"feature": "ofs_pct", "value": -2.4, "direction": "increases_risk", "display_name": "High OFS (promoter exit)"},
                {"feature": "valuation_premium", "value": -2.2, "direction": "increases_risk", "display_name": "Extreme Valuation"},
                {"feature": "debt_equity_ratio", "value": -1.6, "direction": "increases_risk", "display_name": "Debt Level"},
                {"feature": "revenue_growth_yoy", "value": 1.2, "direction": "decreases_risk", "display_name": "Revenue Growth"},
            ],
            "fraud_flags": [
                {"rule_id": "FR001", "severity": "high", "description": "Sustained losses with no clear path to profitability in prospectus"},
                {"rule_id": "FR002", "severity": "medium", "description": "High OFS proportion — promoters reducing stake significantly"},
                {"rule_id": "FR005", "severity": "medium", "description": "Regulatory risk: RBI scrutiny on payment aggregator license"},
            ],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 42.6, "peer_ev_ebitda_median": 28.4,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "BAJFINANCE", "name": "Bajaj Finance", "pe": 34.2, "ev_ebitda": 26.8, "market_cap_cr": 420000},
                {"ticker": "HDFCBANK", "name": "HDFC Bank", "pe": 18.4, "ev_ebitda": 14.2, "market_cap_cr": 1240000},
            ],
        },
        "_subscription": {"qib_predicted": 2.79, "hni_predicted": 3.53, "rii_predicted": 1.05,
                          "overall_predicted": 1.89, "allotment_probability": 0.75},
    },
    # ── 11. Campus Activewear ─────────────────────────────────────────────────
    {
        "ipo": {
            "id": "campus_2022", "company_name": "Campus Activewear", "sector": "Retail",
            "status": "listed", "issue_size_cr": 1400, "price_band_low": 278, "price_band_high": 292,
            "listing_date": "2022-05-09", "listing_gain_pct": 21.0, "promoter_stake_pre": 62.4,
            "ofs_pct": 100.0, "fresh_issue_pct": 0.0,
            "financial_score": 70, "sentiment_score": 65, "risk_score": 35,
            "risk_label": "Low", "confidence_score": 67, "valuation_label": "Fair",
            "overall_sub_multiple": 51.75,
        },
        "_financial": {"profitability_score": 72, "growth_score": 74, "liquidity_score": 68,
                       "solvency_score": 70, "efficiency_score": 66},
        "_sentiment": {"score": 65, "label": "positive", "positive_pct": 52, "neutral_pct": 32,
                       "negative_pct": 16, "top_keywords": ["campus", "footwear", "athletic", "d2c", "growth"],
                       "news_volume_7d": 62},
        "_risk": {
            "risk_score": 35, "risk_label": "Low", "prob_low": 0.56, "prob_medium": 0.36, "prob_high": 0.08,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 1.8, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "roce", "value": 1.4, "direction": "decreases_risk", "display_name": "ROCE"},
                {"feature": "ofs_pct", "value": -1.2, "direction": "increases_risk", "display_name": "Full OFS"},
                {"feature": "promoter_stake_pre", "value": 1.0, "direction": "decreases_risk", "display_name": "Promoter Stake"},
                {"feature": "net_profit_margin", "value": 0.8, "direction": "decreases_risk", "display_name": "Profit Margin"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 54.2, "peer_pe_median": 48.6, "peer_ev_ebitda_median": 28.4,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "BATAINDIA", "name": "Bata India", "pe": 48.4, "ev_ebitda": 24.2, "market_cap_cr": 10200},
                {"ticker": "RELAXO", "name": "Relaxo Footwears", "pe": 52.8, "ev_ebitda": 32.1, "market_cap_cr": 8400},
                {"ticker": "VMART", "name": "V-Mart Retail", "pe": 38.6, "ev_ebitda": 18.4, "market_cap_cr": 3200},
            ],
        },
        "_subscription": {"qib_predicted": 101.4, "hni_predicted": 44.8, "rii_predicted": 7.4,
                          "overall_predicted": 51.75, "allotment_probability": 0.09},
    },
    # ── 12. Harsha Engineers ──────────────────────────────────────────────────
    {
        "ipo": {
            "id": "harsha_eng_2022", "company_name": "Harsha Engineers International", "sector": "Manufacturing",
            "status": "listed", "issue_size_cr": 755, "price_band_low": 314, "price_band_high": 330,
            "listing_date": "2022-09-26", "listing_gain_pct": 35.5, "promoter_stake_pre": 70.2,
            "ofs_pct": 48.0, "fresh_issue_pct": 52.0,
            "financial_score": 75, "sentiment_score": 68, "risk_score": 30,
            "risk_label": "Low", "confidence_score": 72, "valuation_label": "Fair",
            "overall_sub_multiple": 74.7,
        },
        "_financial": {"profitability_score": 76, "growth_score": 72, "liquidity_score": 74,
                       "solvency_score": 78, "efficiency_score": 75},
        "_sentiment": {"score": 68, "label": "positive", "positive_pct": 55, "neutral_pct": 32,
                       "negative_pct": 13, "top_keywords": ["harsha", "bearing", "export", "manufacturing", "auto"],
                       "news_volume_7d": 48},
        "_risk": {
            "risk_score": 30, "risk_label": "Low", "prob_low": 0.62, "prob_medium": 0.32, "prob_high": 0.06,
            "shap_top_drivers": [
                {"feature": "promoter_stake_pre", "value": 1.8, "direction": "decreases_risk", "display_name": "High Promoter Stake"},
                {"feature": "roce", "value": 1.6, "direction": "decreases_risk", "display_name": "ROCE"},
                {"feature": "net_profit_margin", "value": 1.2, "direction": "decreases_risk", "display_name": "Profit Margin"},
                {"feature": "revenue_growth_yoy", "value": 1.0, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "cash_conversion_cycle", "value": -0.8, "direction": "increases_risk", "display_name": "Working Capital Cycle"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 22.4, "peer_pe_median": 24.8, "peer_ev_ebitda_median": 14.6,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "SCHAEFFLER", "name": "Schaeffler India", "pe": 46.2, "ev_ebitda": 28.4, "market_cap_cr": 25000},
                {"ticker": "SKF", "name": "SKF India", "pe": 38.8, "ev_ebitda": 22.6, "market_cap_cr": 16000},
                {"ticker": "TIMKEN", "name": "Timken India", "pe": 38.4, "ev_ebitda": 22.1, "market_cap_cr": 9200},
            ],
        },
        "_subscription": {"qib_predicted": 158.4, "hni_predicted": 82.1, "rii_predicted": 10.8,
                          "overall_predicted": 74.7, "allotment_probability": 0.07},
    },
    # ── 13. Swiggy ────────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "swiggy_2024", "company_name": "Swiggy Ltd", "sector": "Food & Delivery",
            "status": "listed", "issue_size_cr": 11327, "price_band_low": 371, "price_band_high": 390,
            "listing_date": "2024-11-13", "listing_gain_pct": 5.6, "promoter_stake_pre": 8.0,
            "ofs_pct": 44.0, "fresh_issue_pct": 56.0,
            "financial_score": 52, "sentiment_score": 74, "risk_score": 62,
            "risk_label": "Medium", "confidence_score": 58, "valuation_label": "Expensive",
            "overall_sub_multiple": 3.59,
        },
        "_financial": {"profitability_score": 28, "growth_score": 82, "liquidity_score": 56,
                       "solvency_score": 48, "efficiency_score": 54},
        "_sentiment": {"score": 74, "label": "positive", "positive_pct": 60, "neutral_pct": 28,
                       "negative_pct": 12, "top_keywords": ["swiggy", "delivery", "zomato", "quick_commerce", "losses"],
                       "news_volume_7d": 284},
        "_risk": {
            "risk_score": 62, "risk_label": "Medium", "prob_low": 0.14, "prob_medium": 0.42, "prob_high": 0.44,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": -3.0, "direction": "increases_risk", "display_name": "Ongoing Losses"},
                {"feature": "revenue_growth_yoy", "value": 2.0, "direction": "decreases_risk", "display_name": "GMV Growth"},
                {"feature": "cash_conversion_cycle", "value": -1.6, "direction": "increases_risk", "display_name": "Cash Burn"},
                {"feature": "gmp_premium", "value": 0.6, "direction": "decreases_risk", "display_name": "GMP Marginal Positive"},
                {"feature": "valuation_premium", "value": -1.2, "direction": "increases_risk", "display_name": "High Valuation vs Peers"},
            ],
            "fraud_flags": [
                {"rule_id": "FR001", "severity": "medium", "description": "Continued EBITDA losses in core food delivery segment"},
            ],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 45.2, "peer_ev_ebitda_median": 30.4,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "ZOMATO", "name": "Zomato", "pe": 220.4, "ev_ebitda": 68.2, "market_cap_cr": 218000},
                {"ticker": "JUBLFOOD", "name": "Jubilant FoodWorks", "pe": 48.3, "ev_ebitda": 32.1, "market_cap_cr": 38000},
            ],
        },
        "_subscription": {"qib_predicted": 6.8, "hni_predicted": 2.4, "rii_predicted": 0.9,
                          "overall_predicted": 3.59, "allotment_probability": 0.58},
    },
    # ── 14. FirstCry ──────────────────────────────────────────────────────────
    {
        "ipo": {
            "id": "firstcry_2024", "company_name": "Brainbees Solutions (FirstCry)", "sector": "Consumer",
            "status": "open", "issue_size_cr": 4193, "price_band_low": 440, "price_band_high": 465,
            "open_date": "2026-04-20", "close_date": "2026-04-23",
            "financial_score": 58, "sentiment_score": 68, "risk_score": 58,
            "risk_label": "Medium", "confidence_score": 60, "valuation_label": "Fair",
            "overall_sub_multiple": 12.0,
        },
        "_financial": {"profitability_score": 40, "growth_score": 72, "liquidity_score": 60,
                       "solvency_score": 55, "efficiency_score": 62},
        "_sentiment": {"score": 68, "label": "positive", "positive_pct": 52, "neutral_pct": 34,
                       "negative_pct": 14, "top_keywords": ["firstcry", "baby", "omnichannel", "softbank", "retail"],
                       "news_volume_7d": 96},
        "_risk": {
            "risk_score": 58, "risk_label": "Medium", "prob_low": 0.18, "prob_medium": 0.46, "prob_high": 0.36,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": -2.0, "direction": "increases_risk", "display_name": "Pre-Profit Stage"},
                {"feature": "revenue_growth_yoy", "value": 1.6, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "promoter_stake_pre", "value": -0.8, "direction": "increases_risk", "display_name": "Founder Dilution"},
                {"feature": "brand_strength", "value": 1.2, "direction": "decreases_risk", "display_name": "Brand Leadership"},
                {"feature": "cash_conversion_cycle", "value": -1.0, "direction": "increases_risk", "display_name": "Working Capital"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 58.4, "peer_ev_ebitda_median": 32.2,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "TRENT", "name": "Trent Ltd", "pe": 112.4, "ev_ebitda": 62.1, "market_cap_cr": 165000},
                {"ticker": "SHOPERSTOP", "name": "Shoppers Stop", "pe": 58.2, "ev_ebitda": 22.4, "market_cap_cr": 9200},
                {"ticker": "VMART", "name": "V-Mart Retail", "pe": 38.6, "ev_ebitda": 18.4, "market_cap_cr": 3200},
            ],
        },
        "_subscription": {"qib_predicted": 24.2, "hni_predicted": 9.8, "rii_predicted": 2.8,
                          "overall_predicted": 12.0, "allotment_probability": 0.38},
    },
    # ── 15. TechIndia Solutions (demo open) ───────────────────────────────────
    {
        "ipo": {
            "id": "demo_ipo_1", "company_name": "TechIndia Solutions", "sector": "IT Services",
            "status": "open", "issue_size_cr": 2500, "price_band_low": 380, "price_band_high": 400,
            "open_date": "2026-04-21", "close_date": "2026-04-24",
            "promoter_stake_pre": 62.0, "ofs_pct": 30.0, "fresh_issue_pct": 70.0,
            "financial_score": 78, "sentiment_score": 74, "risk_score": 26,
            "risk_label": "Low", "confidence_score": 76, "valuation_label": "Fair",
            "overall_sub_multiple": 28.5,
        },
        "_financial": {"profitability_score": 80, "growth_score": 76, "liquidity_score": 78,
                       "solvency_score": 80, "efficiency_score": 76},
        "_sentiment": {"score": 74, "label": "positive", "positive_pct": 60, "neutral_pct": 28,
                       "negative_pct": 12, "top_keywords": ["techIndia", "saas", "engineering", "export", "profitability"],
                       "news_volume_7d": 84},
        "_risk": {
            "risk_score": 26, "risk_label": "Low", "prob_low": 0.68, "prob_medium": 0.26, "prob_high": 0.06,
            "shap_top_drivers": [
                {"feature": "roce", "value": 2.2, "direction": "decreases_risk", "display_name": "Strong ROCE"},
                {"feature": "net_profit_margin", "value": 1.8, "direction": "decreases_risk", "display_name": "Profit Margin"},
                {"feature": "revenue_growth_yoy", "value": 1.6, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "promoter_stake_pre", "value": 1.2, "direction": "decreases_risk", "display_name": "Promoter Stake"},
                {"feature": "debt_equity_ratio", "value": -0.6, "direction": "increases_risk", "display_name": "Moderate Leverage"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 24.8, "peer_pe_median": 26.4, "peer_ev_ebitda_median": 16.8,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "INFY", "name": "Infosys", "pe": 27.8, "ev_ebitda": 17.2, "market_cap_cr": 620000},
                {"ticker": "WIPRO", "name": "Wipro", "pe": 21.3, "ev_ebitda": 14.8, "market_cap_cr": 245000},
                {"ticker": "MPHASIS", "name": "Mphasis", "pe": 28.4, "ev_ebitda": 18.6, "market_cap_cr": 48000},
            ],
        },
        "_subscription": {"qib_predicted": 58.4, "hni_predicted": 22.8, "rii_predicted": 5.6,
                          "overall_predicted": 28.5, "allotment_probability": 0.16},
    },
    # ── 16. GreenPower Energy (demo open) ─────────────────────────────────────
    {
        "ipo": {
            "id": "demo_ipo_2", "company_name": "GreenPower Energy", "sector": "Renewable Energy",
            "status": "open", "issue_size_cr": 1800, "price_band_low": 250, "price_band_high": 265,
            "open_date": "2026-04-20", "close_date": "2026-04-23",
            "promoter_stake_pre": 58.5, "ofs_pct": 20.0, "fresh_issue_pct": 80.0,
            "financial_score": 62, "sentiment_score": 82, "risk_score": 44,
            "risk_label": "Medium", "confidence_score": 68, "valuation_label": "Fair",
            "overall_sub_multiple": 18.2,
        },
        "_financial": {"profitability_score": 55, "growth_score": 72, "liquidity_score": 60,
                       "solvency_score": 58, "efficiency_score": 65},
        "_sentiment": {"score": 82, "label": "positive", "positive_pct": 68, "neutral_pct": 24,
                       "negative_pct": 8, "top_keywords": ["renewable", "solar", "greenpower", "net_zero", "energy_transition"],
                       "news_volume_7d": 118},
        "_risk": {
            "risk_score": 44, "risk_label": "Medium", "prob_low": 0.32, "prob_medium": 0.50, "prob_high": 0.18,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 2.0, "direction": "decreases_risk", "display_name": "Capacity Growth"},
                {"feature": "gmp_premium", "value": 1.4, "direction": "decreases_risk", "display_name": "GMP Positive"},
                {"feature": "debt_equity_ratio", "value": -2.2, "direction": "increases_risk", "display_name": "Capital-Intensive Leverage"},
                {"feature": "cash_conversion_cycle", "value": -1.0, "direction": "increases_risk", "display_name": "Long Project Cycle"},
                {"feature": "fresh_issue_pct", "value": 1.0, "direction": "decreases_risk", "display_name": "Capital for Expansion"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 28.6, "peer_pe_median": 32.4, "peer_ev_ebitda_median": 18.6,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "ADANIGREEN", "name": "Adani Green Energy", "pe": 124.4, "ev_ebitda": 42.6, "market_cap_cr": 320000},
                {"ticker": "TATAPOWER", "name": "Tata Power", "pe": 42.8, "ev_ebitda": 14.2, "market_cap_cr": 130000},
                {"ticker": "GREENKO", "name": "Greenko Group (private)", "pe": None, "ev_ebitda": 22.4, "market_cap_cr": None},
            ],
        },
        "_subscription": {"qib_predicted": 38.2, "hni_predicted": 15.6, "rii_predicted": 3.8,
                          "overall_predicted": 18.2, "allotment_probability": 0.24},
    },
    # ── 17. HealthFirst Diagnostics (upcoming) ────────────────────────────────
    {
        "ipo": {
            "id": "demo_ipo_3", "company_name": "HealthFirst Diagnostics", "sector": "Healthcare",
            "status": "upcoming", "issue_size_cr": 950, "price_band_low": 190, "price_band_high": 200,
            "open_date": "2026-04-28",
            "promoter_stake_pre": 68.0, "ofs_pct": 40.0, "fresh_issue_pct": 60.0,
            "financial_score": 80, "sentiment_score": 70, "risk_score": 28,
            "risk_label": "Low", "confidence_score": 75, "valuation_label": "Fair",
            "overall_sub_multiple": 42.0,
        },
        "_financial": {"profitability_score": 82, "growth_score": 78, "liquidity_score": 80,
                       "solvency_score": 82, "efficiency_score": 78},
        "_sentiment": {"score": 70, "label": "positive", "positive_pct": 56, "neutral_pct": 32,
                       "negative_pct": 12, "top_keywords": ["diagnostics", "healthcare", "labs", "growth", "india"],
                       "news_volume_7d": 68},
        "_risk": {
            "risk_score": 28, "risk_label": "Low", "prob_low": 0.66, "prob_medium": 0.28, "prob_high": 0.06,
            "shap_top_drivers": [
                {"feature": "net_profit_margin", "value": 2.0, "direction": "decreases_risk", "display_name": "Profit Margin"},
                {"feature": "promoter_stake_pre", "value": 1.8, "direction": "decreases_risk", "display_name": "Promoter Stake"},
                {"feature": "roce", "value": 1.6, "direction": "decreases_risk", "display_name": "ROCE"},
                {"feature": "revenue_growth_yoy", "value": 1.4, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "ofs_pct", "value": -0.8, "direction": "increases_risk", "display_name": "Partial OFS"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 30.4, "peer_pe_median": 42.8, "peer_ev_ebitda_median": 26.4,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "DRREDDY", "name": "Dr Lal PathLabs", "pe": 48.4, "ev_ebitda": 28.6, "market_cap_cr": 18000},
                {"ticker": "METROPOLIS", "name": "Metropolis Healthcare", "pe": 42.1, "ev_ebitda": 24.8, "market_cap_cr": 6200},
                {"ticker": "THYROCARE", "name": "Thyrocare Technologies", "pe": 32.6, "ev_ebitda": 18.4, "market_cap_cr": 2800},
            ],
        },
        "_subscription": {"qib_predicted": 88.4, "hni_predicted": 36.2, "rii_predicted": 8.4,
                          "overall_predicted": 42.0, "allotment_probability": 0.11},
    },
    # ── 18. SmartEdu Platform (upcoming) ─────────────────────────────────────
    {
        "ipo": {
            "id": "demo_ipo_5", "company_name": "SmartEdu Platform", "sector": "EdTech",
            "status": "upcoming", "issue_size_cr": 1200, "price_band_low": 280, "price_band_high": 295,
            "open_date": "2026-04-29",
            "promoter_stake_pre": 48.0, "ofs_pct": 35.0, "fresh_issue_pct": 65.0,
            "financial_score": 60, "sentiment_score": 65, "risk_score": 50,
            "risk_label": "Medium", "confidence_score": 62, "valuation_label": "Fair",
            "overall_sub_multiple": 22.5,
        },
        "_financial": {"profitability_score": 52, "growth_score": 74, "liquidity_score": 62,
                       "solvency_score": 58, "efficiency_score": 54},
        "_sentiment": {"score": 65, "label": "positive", "positive_pct": 50, "neutral_pct": 34,
                       "negative_pct": 16, "top_keywords": ["edtech", "learning", "k12", "revenue", "growth"],
                       "news_volume_7d": 72},
        "_risk": {
            "risk_score": 50, "risk_label": "Medium", "prob_low": 0.24, "prob_medium": 0.50, "prob_high": 0.26,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 1.8, "direction": "decreases_risk", "display_name": "Student Growth"},
                {"feature": "net_profit_margin", "value": -1.6, "direction": "increases_risk", "display_name": "Thin Margins"},
                {"feature": "promoter_stake_pre", "value": -0.8, "direction": "increases_risk", "display_name": "Promoter Dilution Risk"},
                {"feature": "cash_conversion_cycle", "value": -1.0, "direction": "increases_risk", "display_name": "Content Investment Cycle"},
                {"feature": "brand_strength", "value": 0.8, "direction": "decreases_risk", "display_name": "Brand Recognition"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 48.4, "peer_ev_ebitda_median": 28.6,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "CARERATING", "name": "CARE Ratings", "pe": 22.4, "ev_ebitda": 14.8, "market_cap_cr": 4200},
                {"ticker": "NIIT", "name": "NIIT Ltd", "pe": 28.6, "ev_ebitda": 18.2, "market_cap_cr": 2800},
            ],
        },
        "_subscription": {"qib_predicted": 46.4, "hni_predicted": 18.8, "rii_predicted": 4.2,
                          "overall_predicted": 22.5, "allotment_probability": 0.20},
    },
    # ── 19. IndusRenew Power (upcoming) ───────────────────────────────────────
    {
        "ipo": {
            "id": "demo_ipo_6", "company_name": "IndusRenew Power", "sector": "Renewable Energy",
            "status": "upcoming", "issue_size_cr": 2200, "price_band_low": 185, "price_band_high": 195,
            "open_date": "2026-04-30",
            "promoter_stake_pre": 72.0, "ofs_pct": 25.0, "fresh_issue_pct": 75.0,
            "financial_score": 70, "sentiment_score": 76, "risk_score": 36,
            "risk_label": "Low", "confidence_score": 71, "valuation_label": "Fair",
            "overall_sub_multiple": 32.4,
        },
        "_financial": {"profitability_score": 68, "growth_score": 78, "liquidity_score": 66,
                       "solvency_score": 70, "efficiency_score": 68},
        "_sentiment": {"score": 76, "label": "positive", "positive_pct": 62, "neutral_pct": 28,
                       "negative_pct": 10, "top_keywords": ["indusrenew", "solar", "wind", "renewable", "ppa"],
                       "news_volume_7d": 82},
        "_risk": {
            "risk_score": 36, "risk_label": "Low", "prob_low": 0.56, "prob_medium": 0.36, "prob_high": 0.08,
            "shap_top_drivers": [
                {"feature": "revenue_growth_yoy", "value": 2.0, "direction": "decreases_risk", "display_name": "Capacity Growth"},
                {"feature": "fresh_issue_pct", "value": 1.4, "direction": "decreases_risk", "display_name": "Expansion Capital"},
                {"feature": "promoter_stake_pre", "value": 1.2, "direction": "decreases_risk", "display_name": "Promoter Commitment"},
                {"feature": "debt_equity_ratio", "value": -1.8, "direction": "increases_risk", "display_name": "Project Finance Debt"},
                {"feature": "cash_conversion_cycle", "value": -0.8, "direction": "increases_risk", "display_name": "Long Gestation Period"},
            ],
            "fraud_flags": [],
        },
        "_peers": {
            "ipo_pe": 32.8, "peer_pe_median": 48.6, "peer_ev_ebitda_median": 22.4,
            "valuation_label": "Fair",
            "peers": [
                {"ticker": "TATAPOWER", "name": "Tata Power Renewables", "pe": 42.8, "ev_ebitda": 14.2, "market_cap_cr": 130000},
                {"ticker": "NTPC", "name": "NTPC Green Energy", "pe": 28.4, "ev_ebitda": 12.8, "market_cap_cr": 340000},
            ],
        },
        "_subscription": {"qib_predicted": 68.4, "hni_predicted": 26.8, "rii_predicted": 5.8,
                          "overall_predicted": 32.4, "allotment_probability": 0.14},
    },
    # ── 20. AgriTech Ventures (upcoming, High risk) ───────────────────────────
    {
        "ipo": {
            "id": "demo_ipo_4", "company_name": "AgriTech Ventures", "sector": "Agriculture",
            "status": "upcoming", "issue_size_cr": 600, "price_band_low": 120, "price_band_high": 128,
            "open_date": "2026-04-30",
            "promoter_stake_pre": 40.0, "ofs_pct": 55.0, "fresh_issue_pct": 45.0,
            "financial_score": 55, "sentiment_score": 58, "risk_score": 72,
            "risk_label": "High", "confidence_score": 45, "valuation_label": "Expensive",
            "overall_sub_multiple": 8.4,
        },
        "_financial": {"profitability_score": 42, "growth_score": 62, "liquidity_score": 52,
                       "solvency_score": 48, "efficiency_score": 58},
        "_sentiment": {"score": 58, "label": "neutral", "positive_pct": 40, "neutral_pct": 38,
                       "negative_pct": 22, "top_keywords": ["agritech", "farming", "drones", "startup", "subsidy"],
                       "news_volume_7d": 42},
        "_risk": {
            "risk_score": 72, "risk_label": "High", "prob_low": 0.08, "prob_medium": 0.26, "prob_high": 0.66,
            "shap_top_drivers": [
                {"feature": "ofs_pct", "value": -2.4, "direction": "increases_risk", "display_name": "High OFS Ratio"},
                {"feature": "net_profit_margin", "value": -2.0, "direction": "increases_risk", "display_name": "Pre-Profit Stage"},
                {"feature": "promoter_stake_pre", "value": -1.6, "direction": "increases_risk", "display_name": "Low Promoter Skin"},
                {"feature": "revenue_growth_yoy", "value": 1.2, "direction": "decreases_risk", "display_name": "Revenue Growth"},
                {"feature": "cash_conversion_cycle", "value": -1.0, "direction": "increases_risk", "display_name": "Seasonal Working Capital"},
            ],
            "fraud_flags": [
                {"rule_id": "FR002", "severity": "high", "description": "OFS proportion exceeds 50% — primary promoter exit signal"},
                {"rule_id": "FR003", "severity": "medium", "description": "Revenue concentration in top 3 customers exceeds 60%"},
            ],
        },
        "_peers": {
            "ipo_pe": None, "peer_pe_median": 18.4, "peer_ev_ebitda_median": 12.6,
            "valuation_label": "Expensive",
            "peers": [
                {"ticker": "RALLIS", "name": "Rallis India", "pe": 22.4, "ev_ebitda": 12.8, "market_cap_cr": 4200},
                {"ticker": "KAVERI", "name": "Kaveri Seed Company", "pe": 14.6, "ev_ebitda": 10.4, "market_cap_cr": 3200},
            ],
        },
        "_subscription": {"qib_predicted": 18.4, "hni_predicted": 6.8, "rii_predicted": 1.6,
                          "overall_predicted": 8.4, "allotment_probability": 0.42},
    },
]


# ─── FinBERT input headlines per demo IPO ────────────────────────────────────
# 3-4 realistic financial news headlines per IPO for FinBERT sentiment scoring.

DEMO_HEADLINES: dict[str, list[str]] = {
    # Headlines are written in standard financial earnings/market language
    # (not IPO subscription jargon) so FinBERT classifies them accurately.
    "tata_tech_2023": [
        "Tata Technologies revenue grew 18 percent on strong engineering R&D services demand",
        "Analysts raised price target on Tata Technologies citing EV software tailwinds",
        "Strong institutional confidence and robust order book reinforce Tata Tech growth outlook",
        "Tata Technologies reported strong profitability with improving return on capital employed",
    ],
    "hyundai_india_2024": [
        "Hyundai Motor India listed at parity raising concerns about premium valuation",
        "Analysts remain divided on Hyundai India amid intense competition from Maruti Suzuki",
        "Full promoter stake sale structure raises concerns about commitment to India business",
        "Strong SUV portfolio and EV pipeline support Hyundai India medium-term revenue growth",
    ],
    "bajaj_housing_2024": [
        "Bajaj Housing Finance posted 26 percent NIM expansion backed by retail mortgage demand",
        "Loan book grew strongly as Bajaj Housing Finance capitalised on housing demand surge",
        "Strong Bajaj group brand drives institutional confidence and positive outlook",
        "Capital adequacy strengthened boosting Bajaj Housing Finance capacity for growth",
    ],
    "zomato_2021": [
        "Zomato revenue grew strongly as food delivery demand recovered post pandemic",
        "Analysts bullish on Zomato long-term profitability as market leadership solidifies",
        "Zomato reported record daily orders driven by robust consumer demand",
        "Zomato Hyperpure B2B segment emerging as high-margin revenue contributor",
    ],
    "nykaa_2021": [
        "Nykaa achieved EBITDA profitability setting it apart from other consumer tech peers",
        "Revenue grew strongly as Nykaa expanded omnichannel beauty retail footprint",
        "Strong brand loyalty and repeat purchase rate underpin Nykaa competitive advantage",
        "Analysts positive on Nykaa premium valuation given first-mover advantage in beauty",
    ],
    "lic_2022": [
        "LIC reported strong premium income growth backed by India life insurance market expansion",
        "LIC monopoly position and brand strength remain significant competitive advantages",
        "LIC shares declined at listing as valuation premium seen as stretched by analysts",
        "Government divestment structure raised overhang concerns though fundamentals remain solid",
    ],
    "policybazaar_2021": [
        "PolicyBazaar revenue grew strongly as digital insurance platform gained market share",
        "Analysts positive on PB Fintech long-term opportunity in underpenetrated insurance market",
        "Heavy losses and elevated cash burn remain concerns despite strong top-line growth",
        "PB Fintech investments in credit and renewal segments seen as value drivers",
    ],
    "delhivery_2022": [
        "Delhivery revenue grew as e-commerce logistics volumes expanded significantly",
        "Delhivery reported losses as margins remain under pressure from high operating costs",
        "Analysts mixed on Delhivery with revenue growth offset by weak profitability metrics",
        "Delhivery B2B expansion seen as positive step but cash burn remains a concern",
    ],
    "ola_electric_2024": [
        "Ola Electric revenue grew strongly driven by robust EV scooter demand in India",
        "Analysts bullish on Ola Electric Gigafactory scale advantage and cost reduction trajectory",
        "Government FAME subsidy support boosted Ola Electric demand and order pipeline",
        "Strong brand recognition and retail demand reinforce Ola Electric growth case",
    ],
    "paytm_2021": [
        "Paytm share price plunged 27 percent at listing on extreme valuation concerns",
        "Paytm reported persistent losses with no clear profitability timeline disclosed",
        "RBI regulatory risk poses major overhang on Paytm payment aggregator business",
        "High promoter stake sale signals exit concerns as losses continue to mount",
    ],
    "campus_2022": [
        "Campus Activewear revenue grew with improving margins as D2C channel scaled up",
        "Analysts positive on Campus Activewear margin expansion and profitable growth",
        "Strong promoter commitment and asset-light model reinforced investor confidence",
        "Campus targets premium athletic footwear segment as direct sales channel gains share",
    ],
    "harsha_eng_2022": [
        "Harsha Engineers reported strong revenue growth backed by global auto sector recovery",
        "Analysts raised estimates on Harsha Engineers citing strong ROCE and cash flows",
        "Capacity expansion to serve global bearing clients reinforces positive growth outlook",
        "Harsha Engineers dominant market position in bearing cages supports pricing power",
    ],
    "swiggy_2024": [
        "Swiggy Instamart quick commerce revenue grew strongly as consumer adoption accelerated",
        "Analysts cautiously optimistic on Swiggy path toward EBITDA breakeven by FY26",
        "Swiggy competitive battle with Zomato keeps marketing and delivery costs elevated",
        "Fresh capital enables Swiggy to accelerate quick commerce expansion in tier two cities",
    ],
    "firstcry_2024": [
        "FirstCry revenue grew as omnichannel baby and kids retail business expanded",
        "Analysts positive on FirstCry long-term growth driven by India young parent demographic",
        "Continued losses in core operations weigh on FirstCry near-term profitability outlook",
        "FirstCry international expansion adds geographic optionality to the growth story",
    ],
    "demo_ipo_1": [
        "TechIndia Solutions revenue grew 22 percent as global clients expanded India delivery centres",
        "Analysts initiated Buy on TechIndia citing strong EBITDA margins and cash generation",
        "Strong order book and multi-year SaaS contract wins underpin TechIndia growth outlook",
        "TechIndia reported improving return on equity and strong operating cash flows",
    ],
    "demo_ipo_2": [
        "GreenPower Energy capacity grew strongly backed by government renewable energy push",
        "Long-term power purchase agreements provide GreenPower strong revenue visibility",
        "Analysts bullish on GreenPower Energy as India accelerates clean energy transition",
        "GreenPower secured large solar project boosting revenue and earnings outlook",
    ],
    "demo_ipo_3": [
        "HealthFirst Diagnostics revenue grew as preventive health awareness increased post pandemic",
        "Analysts positive on HealthFirst high ROCE and durable asset-light franchise model",
        "Strong demand for organised diagnostics supports HealthFirst sustained revenue growth",
        "HealthFirst expanded lab network to 250 centres reinforcing competitive market position",
    ],
    "demo_ipo_5": [
        "SmartEdu Platform gross margins improved as digital learning content scaled up",
        "Analysts cautiously positive on SmartEdu as K-12 online tutoring adoption grew",
        "Path to profitability depends on reducing student acquisition costs say analysts",
        "SmartEdu revenue grew as paid learner base expanded toward five million target",
    ],
    "demo_ipo_6": [
        "IndusRenew Power revenue grew backed by long-term power purchase agreements",
        "Analysts positive on IndusRenew diversified renewable capacity expansion pipeline",
        "Strong promoter commitment and capital allocation reinforce IndusRenew growth outlook",
        "IndusRenew secured multiple solar and wind projects improving earnings visibility",
    ],
    "demo_ipo_4": [
        "AgriTech Ventures reported losses and revenue concentrated in top three clients",
        "Analysts cautious as high promoter stake sale signals exit concerns at listing",
        "Dependency on government subsidies and seasonal cash flows raise risk concerns",
        "Customer concentration risk and thin margins weigh on AgriTech Ventures outlook",
    ],
}


# ─── Main seed function ───────────────────────────────────────────────────────

async def seed():
    await init_db()
    async with SessionLocal() as db:
        if os.path.exists(MASTER_CSV):
            await _seed_from_csv(db)
        else:
            print(f"[INFO] {MASTER_CSV} not found. Inserting 20 curated demo IPOs.")
            await _insert_demo_data(db)


async def _seed_from_csv(db):
    df = pd.read_csv(MASTER_CSV)
    print(f"[INFO] Loaded {len(df)} rows from {MASTER_CSV}")
    sent_map = {}
    if os.path.exists(SENTIMENT_CSV):
        sent_df = pd.read_csv(SENTIMENT_CSV)
        sent_map = dict(zip(sent_df["ipo_id"], sent_df.to_dict("records")))

    inserted = 0
    for _, row in df.iterrows():
        ipo_id = str(row.get("ipo_id", _make_id(str(row.get("company_name", "")), str(row.get("year", "2024")))))
        if await db.get(IPO, ipo_id):
            continue

        ipo = IPO(
            id=ipo_id, company_name=str(row.get("company_name", "Unknown")),
            sector=str(row.get("sector", "Others")),
            issue_size_cr=_f(row.get("issue_size_cr")), price_band_low=_f(row.get("price_band_low")),
            price_band_high=_f(row.get("price_band_high")), open_date=_s(row.get("open_date")),
            close_date=_s(row.get("close_date")), listing_date=_s(row.get("listing_date")),
            status=_s(row.get("status", "listed")), listing_price=_f(row.get("listing_price")),
            listing_gain_pct=_f(row.get("listing_gain_pct")), gmp_t3=_f(row.get("gmp_t3")),
            promoter_stake_pre=_f(row.get("promoter_stake_pre")), ofs_pct=_f(row.get("ofs_pct")),
            fresh_issue_pct=_f(row.get("fresh_issue_pct")),
        )
        fin_cols = ["profitability_score", "growth_score", "liquidity_score", "solvency_score", "efficiency_score"]
        if all(c in row for c in fin_cols):
            scores = [_f(row.get(c)) or 0 for c in fin_cols]
            ipo.financial_score = round(sum(scores) / 5, 1)
            db.add(FinancialScore(ipo_id=ipo_id, profitability_score=scores[0], growth_score=scores[1],
                                  liquidity_score=scores[2], solvency_score=scores[3],
                                  efficiency_score=scores[4], overall_score=ipo.financial_score))
        if ipo_id in sent_map:
            s = sent_map[ipo_id]
            ipo.sentiment_score = _f(s.get("score"))
            db.add(SentimentScore(ipo_id=ipo_id, score=ipo.sentiment_score, label=str(s.get("label", "neutral")),
                                  positive_pct=_f(s.get("positive_pct")), neutral_pct=_f(s.get("neutral_pct")),
                                  negative_pct=_f(s.get("negative_pct")), top_keywords=s.get("top_keywords", []),
                                  news_volume_7d=int(s.get("news_volume_7d", 0))))
        _compute_confidence(ipo)
        db.add(ipo)
        inserted += 1
        if inserted % 100 == 0:
            await db.commit()
            print(f"[INFO] Committed {inserted} IPOs...")
    await db.commit()
    print(f"[SUCCESS] Seeded {inserted} IPOs from CSV.")


async def _insert_demo_data(db):
    # Attempt to load FinBERT for authentic sentiment; fall back to static scores if unavailable.
    _analyzer = None
    try:
        from app.ml.finbert_sentiment import FinBERTSentimentAnalyzer
        _analyzer = FinBERTSentimentAnalyzer()
        print("[INFO] FinBERT loaded — computing live sentiment scores for demo IPOs")
    except Exception as exc:
        print(f"[WARN] FinBERT unavailable ({exc}) — using pre-computed sentiment scores")

    inserted = 0
    for entry in DEMO_DATA:
        ipo_data = entry["ipo"]
        ipo_id = ipo_data["id"]
        if await db.get(IPO, ipo_id):
            continue

        ipo = IPO(**ipo_data)
        db.add(ipo)

        fin = entry["_financial"]
        db.add(FinancialScore(
            ipo_id=ipo_id,
            profitability_score=fin["profitability_score"], growth_score=fin["growth_score"],
            liquidity_score=fin["liquidity_score"], solvency_score=fin["solvency_score"],
            efficiency_score=fin["efficiency_score"],
            overall_score=round(sum(fin.values()) / 5, 1),
        ))

        if _analyzer:
            texts = DEMO_HEADLINES.get(ipo_id, []) + [ipo_data["company_name"], ipo_data.get("sector", "")]
            s = _analyzer.analyze([t for t in texts if t])
            print(f"  [{ipo_id}] FinBERT score={s['score']:.1f} label={s['label']}")
            ipo.sentiment_score = s["score"]
        else:
            s = entry["_sentiment"]

        db.add(SentimentScore(
            ipo_id=ipo_id, score=s["score"], label=s["label"],
            positive_pct=s["positive_pct"], neutral_pct=s["neutral_pct"],
            negative_pct=s["negative_pct"], top_keywords=s["top_keywords"],
            news_volume_7d=s["news_volume_7d"],
        ))

        r = entry["_risk"]
        db.add(RiskScore(
            ipo_id=ipo_id, risk_score=r["risk_score"], risk_label=r["risk_label"],
            prob_low=r["prob_low"], prob_medium=r["prob_medium"], prob_high=r["prob_high"],
            shap_top_drivers=r["shap_top_drivers"], fraud_flags=r["fraud_flags"],
        ))

        p = entry["_peers"]
        db.add(PeerData(
            ipo_id=ipo_id, ipo_pe=p["ipo_pe"], peer_pe_median=p["peer_pe_median"],
            peer_ev_ebitda_median=p["peer_ev_ebitda_median"],
            valuation_label=p["valuation_label"], peers=p["peers"],
        ))

        sub = entry["_subscription"]
        db.add(SubscriptionForecast(
            ipo_id=ipo_id, qib_predicted=sub["qib_predicted"], hni_predicted=sub["hni_predicted"],
            rii_predicted=sub["rii_predicted"], overall_predicted=sub["overall_predicted"],
            allotment_probability=sub["allotment_probability"],
        ))

        inserted += 1

    await db.commit()
    print(f"[SUCCESS] Inserted {inserted} curated demo IPOs with full model outputs.")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_id(name: str, year: str) -> str:
    return name.lower().replace(" ", "_").replace(".", "")[:20] + "_" + year


def _compute_confidence(ipo: IPO):
    if not ipo.confidence_score:
        ipo.confidence_score = round(0.5 * (ipo.financial_score or 50)
                                     + 0.3 * (ipo.sentiment_score or 50)
                                     + 0.2 * 50, 1)


def _f(val) -> float | None:
    try:
        return float(val) if pd.notna(val) else None
    except (TypeError, ValueError):
        return None


def _s(val) -> str | None:
    try:
        return str(val) if pd.notna(val) else None
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    asyncio.run(seed())
