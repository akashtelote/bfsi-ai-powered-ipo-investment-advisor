"""
feature_engineering.py — Day 1-2 DS Track script
Transforms ipo_master_raw.csv into clean ipo_master.csv with ~45 model-ready features.

Usage:
    python ml/feature_engineering.py

Input:  ml/data/ipo_master_raw.csv
Output: ml/data/ipo_master.csv   (800 rows × ~45 features)
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SECTOR_ENCODING = {
    "IT Services": 0, "Fintech": 1, "Healthcare": 2, "E-Commerce": 3,
    "BFSI": 4, "Manufacturing": 5, "Consumer": 6, "Infrastructure": 7,
    "Renewable Energy": 8, "Others": 9,
}

# 5-Pillar financial feature groups
PILLAR_FEATURES = {
    "profitability": ["ebitda_margin", "net_margin", "roe", "roce"],
    "growth": ["revenue_cagr_3y", "pat_cagr_3y"],
    "liquidity": ["current_ratio", "cash_ratio"],
    "solvency": ["debt_equity", "interest_coverage"],
    "efficiency": ["asset_turnover", "receivable_days", "inventory_days"],
}

TARGET_COL = "listing_gain_pct"
RISK_TARGET = "risk_label"  # Low/Medium/High (derived from listing_gain_pct)


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[INFO] Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def clean_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include=["object"]).columns:
        # Strip currency symbols and commas
        df[col] = df[col].astype(str).str.replace(r"[₹,% ]", "", regex=True)
        try:
            df[col] = pd.to_numeric(df[col], errors="ignore")
        except Exception:
            pass
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    return df


def derive_features(df: pd.DataFrame) -> pd.DataFrame:
    # Risk label from listing gain
    if TARGET_COL in df.columns:
        df[RISK_TARGET] = pd.cut(
            df[TARGET_COL],
            bins=[-np.inf, 0, 20, np.inf],
            labels=["High", "Medium", "Low"],
        )

    # Sector encoding
    if "sector" in df.columns:
        df["sector_code"] = df["sector"].map(SECTOR_ENCODING).fillna(9).astype(int)

    # Price band width %
    if "price_band_high" in df.columns and "price_band_low" in df.columns:
        df["price_band_width_pct"] = (
            (df["price_band_high"] - df["price_band_low"]) / df["price_band_low"] * 100
        ).clip(0, 20)

    # OFS / Fresh issue split
    if "ofs_pct" not in df.columns and "ofs_amount" in df.columns and "issue_size_cr" in df.columns:
        df["ofs_pct"] = (df["ofs_amount"] / df["issue_size_cr"] * 100).clip(0, 100)
        df["fresh_issue_pct"] = 100 - df["ofs_pct"]

    # Log-transform skewed columns
    for col in ["issue_size_cr", "market_cap_cr"]:
        if col in df.columns:
            df[f"log_{col}"] = np.log1p(df[col].clip(lower=0))

    return df


def compute_pillar_subscores(df: pd.DataFrame) -> pd.DataFrame:
    """Rule-based pillar scoring (0-100) before ML model is trained."""
    for pillar, cols in PILLAR_FEATURES.items():
        available = [c for c in cols if c in df.columns]
        if not available:
            df[f"{pillar}_score"] = 50.0
            continue
        sub = df[available].copy()
        # Normalize each col to 0-100
        for col in available:
            col_min, col_max = sub[col].min(), sub[col].max()
            if col_max > col_min:
                sub[col] = (sub[col] - col_min) / (col_max - col_min) * 100
            else:
                sub[col] = 50.0
        # Invert bad-direction metrics
        invert = ["debt_equity", "receivable_days", "inventory_days"]
        for col in [c for c in invert if c in available]:
            sub[col] = 100 - sub[col]
        df[f"{pillar}_score"] = sub.mean(axis=1).clip(0, 100)

    return df


def compute_confidence_score(df: pd.DataFrame) -> pd.DataFrame:
    fin = df.get("financial_score", df.get("profitability_score", pd.Series([50] * len(df))))
    sent = df.get("sentiment_score", pd.Series([50] * len(df)))
    industry = df.get("efficiency_score", pd.Series([50] * len(df)))
    df["confidence_score"] = (0.5 * fin + 0.3 * sent + 0.2 * industry).clip(0, 100).round(1)
    return df


def select_model_features(df: pd.DataFrame) -> pd.DataFrame:
    financial_feats = [
        "revenue_cagr_3y", "pat_cagr_3y", "ebitda_margin", "net_margin",
        "roe", "roce", "debt_equity", "interest_coverage", "current_ratio",
        "asset_turnover", "receivable_days", "inventory_days",
        "promoter_stake_pre", "ofs_pct", "fresh_issue_pct",
    ]
    market_feats = [
        "log_issue_size_cr", "price_band_width_pct", "gmp_t3", "gmp_t1",
        "nifty_30d_return", "vix_at_open", "sector_code",
        "brlm_reputation_score", "anchor_alloc_pct", "company_age_yrs",
    ]
    subscription_feats = [
        "qib_sub_multiple", "hni_sub_multiple", "rii_sub_multiple",
        "overall_sub_multiple", "allotment_ratio_rii",
    ]
    sentiment_feats = ["sentiment_score", "news_volume_7d"]
    pillar_feats = [f"{p}_score" for p in PILLAR_FEATURES]
    target_feats = [TARGET_COL, RISK_TARGET, "confidence_score"]

    all_feats = financial_feats + market_feats + subscription_feats + sentiment_feats + pillar_feats + target_feats
    available = [c for c in all_feats if c in df.columns]
    return df[available + ["company_name", "sector", "ipo_id"] if "ipo_id" in df.columns else available]


def run():
    raw_path = DATA_DIR / "ipo_master_raw.csv"
    if not raw_path.exists():
        print(f"[ERROR] {raw_path} not found. Run data_collection.py first.")
        return

    df = load_raw(raw_path)
    df = clean_numeric(df)
    df = fill_missing(df)
    df = derive_features(df)
    df = compute_pillar_subscores(df)
    df = compute_confidence_score(df)

    output = select_model_features(df)
    output_path = DATA_DIR / "ipo_master.csv"
    output.to_csv(output_path, index=False)
    print(f"[OK] ipo_master.csv — {len(output)} rows × {len(output.columns)} features")
    print(f"[OK] Written to: {output_path}")

    # Summary stats
    if TARGET_COL in output.columns:
        print(f"\nTarget ({TARGET_COL}) distribution:")
        print(output[TARGET_COL].describe())
    if RISK_TARGET in output.columns:
        print(f"\nRisk label distribution:")
        print(output[RISK_TARGET].value_counts())


if __name__ == "__main__":
    run()
