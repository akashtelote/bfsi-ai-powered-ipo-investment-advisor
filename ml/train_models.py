"""
train_models.py - Day 2-3 DS Track script
Trains all 8 ML models in dependency order and saves .pkl files to ml/models/.

Build order:
    M3 (Financial Health)  ->  M2 (Sentiment, pre-computed)
    M8 (Peer Benchmarking) depends on M3
    M1 (Risk Scoring)      depends on M2 + M3 + M8
    M6 (Subscription)      depends on M1 + M2
    M4 (Listing Price)     depends on M3 + M2
    M7 (Fraud Detection)   rule-based + tree
    M5 (Recommendation)    depends on all above

Usage:
    python ml/train_models.py [--model all | m1 | m2 | m3 | m4 | m5 | m6 | m7 | m8]
"""
import argparse
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
import lightgbm as lgb
import xgboost as xgb
import catboost as cb

DATA_DIR = Path(__file__).parent / "data"
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

RANDOM_SEED = 42


# --- M3: Financial Health Assessment (LightGBM) ---

def train_m3_financial(df: pd.DataFrame):
    print("\n[M3] Training Financial Health Model...")
    feature_cols = [
        "revenue_cagr_3y", "pat_cagr_3y", "ebitda_margin", "net_margin",
        "roe", "roce", "debt_equity", "interest_coverage", "current_ratio",
        "asset_turnover", "receivable_days", "inventory_days",
        "promoter_stake_pre", "ofs_pct", "fresh_issue_pct",
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(df[available].median())
    y = df["listing_gain_pct"].clip(-50, 200)

    model = lgb.LGBMRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        num_leaves=31, subsample=0.8, colsample_bytree=0.8,
        random_state=RANDOM_SEED, n_jobs=-1, verbose=-1,
    )
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"[M3] CV R2 scores: {scores.round(3)} | Mean: {scores.mean():.3f}")

    model.fit(X, y, feature_name=available)
    joblib.dump(model, MODELS_DIR / "financial_model.pkl")
    print(f"[M3] Saved -> {MODELS_DIR / 'financial_model.pkl'}")
    return model


# --- M2: Market Sentiment (FinBERT) ---

def build_m2_sentiment(df: pd.DataFrame):
    """
    Runs FinBERT (ProsusAI/finbert) on per-row headlines or company text.
    Saves a lookup CSV with score, label, and pct breakdowns.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from finbert_sentiment import FinBERTSentimentAnalyzer

    print("\n[M2] Building FinBERT Sentiment Score lookup...")
    analyzer = FinBERTSentimentAnalyzer()

    records = []
    id_col = "ipo_id" if "ipo_id" in df.columns else None

    for _, row in df.iterrows():
        texts: list[str] = []
        if "headlines" in df.columns and pd.notna(row["headlines"]):
            texts = [h.strip() for h in str(row["headlines"]).split("|") if h.strip()]
        if "description" in df.columns and pd.notna(row.get("description")):
            texts.append(str(row["description"])[:256])
        if not texts:
            name = str(row.get("company_name", "")) or str(row.get("issuer_name", ""))
            sector = str(row.get("sector", ""))
            fallback = f"{name} {sector} IPO listing India financial services".strip()
            texts = [fallback]

        result = analyzer.analyze(texts)
        rec = result.copy()
        rec["sentiment_score"] = result["score"]
        rec["sentiment_label"] = result["label"]
        if id_col:
            rec[id_col] = row[id_col]
        records.append(rec)

    out = pd.DataFrame(records)
    df["sentiment_score"] = out["sentiment_score"].values
    df["sentiment_label"] = out["sentiment_label"].values

    csv_cols = ([id_col] if id_col else []) + [
        "sentiment_score", "sentiment_label",
        "positive_pct", "neutral_pct", "negative_pct", "top_keywords", "news_volume_7d",
    ]
    available = [c for c in csv_cols if c in out.columns]
    out[available].to_csv(DATA_DIR / "sentiment_scores.csv", index=False)
    print(f"[M2] FinBERT sentiment_scores.csv saved — {len(out)} rows")
    return df


# --- M8: Peer Benchmarking (K-Means) ---

def train_m8_peers(df: pd.DataFrame):
    print("\n[M8] Training Peer Benchmarking Model (K-Means)...")
    cluster_cols = ["sector_code", "log_issue_size_cr", "roe", "pat_cagr_3y", "debt_equity"]
    available = [c for c in cluster_cols if c in df.columns]
    X = df[available].fillna(df[available].median())

    k = 6
    model = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
    df["cluster_id"] = model.fit_predict(X)

    joblib.dump(model, MODELS_DIR / "peer_model.pkl")
    print(f"[M8] Saved -> {MODELS_DIR / 'peer_model.pkl'}")

    if "sector" in df.columns:
        print(df.groupby(["cluster_id", "sector"]).size().unstack(fill_value=0).to_string())
    return model


# --- M1: IPO Risk Scoring (XGBoost Ensemble) ---

def train_m1_risk(df: pd.DataFrame):
    print("\n[M1] Training IPO Risk Scoring Model (XGBoost)...")
    feature_cols = [
        "financial_score", "sentiment_score", "profitability_score", "growth_score",
        "liquidity_score", "solvency_score", "efficiency_score",
        "revenue_cagr_3y", "pat_cagr_3y", "debt_equity", "roe",
        "gmp_t3", "nifty_30d_return", "vix_at_open", "sector_code",
        "log_issue_size_cr", "ofs_pct", "promoter_stake_pre",
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(df[available].median())

    if "risk_label" not in df.columns:
        df["risk_label"] = pd.cut(
            df["listing_gain_pct"], bins=[-np.inf, 0, 20, np.inf], labels=["High", "Medium", "Low"]
        )

    le = LabelEncoder()
    y = le.fit_transform(df["risk_label"].astype(str))

    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        eval_metric="mlogloss", random_state=RANDOM_SEED, n_jobs=-1,
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")
    print(f"[M1] CV Macro F1: {scores.round(3)} | Mean: {scores.mean():.3f}")

    if scores.mean() < 0.55:
        print("[M1] WARN: F1 < 0.55. Consider simplifying to rule-based risk scoring for demo.")

    model.fit(X, y)
    joblib.dump({"model": model, "label_encoder": le, "features": available}, MODELS_DIR / "risk_model.pkl")
    print(f"[M1] Saved -> {MODELS_DIR / 'risk_model.pkl'}")
    return model


# --- M6: Subscription Demand Forecast (CatBoost) ---

def train_m6_subscription(df: pd.DataFrame):
    print("\n[M6] Training Subscription Demand Forecast (CatBoost)...")
    feature_cols = [
        "log_issue_size_cr", "gmp_t3", "gmp_t1", "sentiment_score",
        "nifty_30d_return", "vix_at_open", "brlm_reputation_score",
        "anchor_alloc_pct", "sector_code", "financial_score",
    ]
    available = [c for c in feature_cols if c in df.columns]

    if "overall_sub_multiple" not in df.columns:
        print("[M6] No subscription target column found - skipping.")
        return None

    X = df[available].fillna(df[available].median())
    y = np.log1p(df["overall_sub_multiple"].clip(lower=0.1))

    model = cb.CatBoostRegressor(
        iterations=300, depth=6, learning_rate=0.05,
        random_seed=RANDOM_SEED, verbose=0,
    )
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"[M6] CV R2 (log subscription): {scores.round(3)} | Mean: {scores.mean():.3f}")

    model.fit(X, y)
    joblib.dump({"model": model, "features": available}, MODELS_DIR / "subscription_model.pkl")
    print(f"[M6] Saved -> {MODELS_DIR / 'subscription_model.pkl'}")
    return model


# --- M4: Listing Price Prediction (Ridge Regression) ---

def train_m4_listing_price(df: pd.DataFrame):
    print("\n[M4] Training Listing Price Prediction Model (Ridge)...")
    feature_cols = [
        "financial_score", "sentiment_score", "gmp_t3", "gmp_t1",
        "nifty_30d_return", "vix_at_open", "overall_sub_multiple",
        "log_issue_size_cr", "sector_code", "ofs_pct", "promoter_stake_pre",
        "ebitda_margin", "net_margin", "roe", "debt_equity",
        "revenue_cagr_3y", "pat_cagr_3y",
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(df[available].median())
    y = df["listing_gain_pct"].clip(-50, 200)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("ridge", Ridge(alpha=1.0)),
    ])
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    print(f"[M4] CV R2 scores: {scores.round(3)} | Mean: {scores.mean():.3f}")

    model.fit(X, y)
    joblib.dump({"model": model, "features": available}, MODELS_DIR / "listing_model.pkl")
    print(f"[M4] Saved -> {MODELS_DIR / 'listing_model.pkl'}")
    return model


# --- M7: Fraud Detection (Rule-based + Decision Tree) ---

def train_m7_fraud(df: pd.DataFrame):
    """
    Fraud detection combines interpretable rules with a decision tree.
    Rules: high OFS, persistent losses, low promoter stake, extreme leverage.
    """
    print("\n[M7] Training Fraud Detection Model (Decision Tree)...")

    flags = pd.Series(0, index=df.index)

    if "ofs_pct" in df.columns:
        flags += (df["ofs_pct"] > 70).astype(int)
    if "net_margin" in df.columns:
        flags += (df["net_margin"] < -15).astype(int)
    if "promoter_stake_pre" in df.columns:
        flags += (df["promoter_stake_pre"] < 30).astype(int)
    if "pat_cagr_3y" in df.columns:
        flags += (df["pat_cagr_3y"] < -30).astype(int)
    if "debt_equity" in df.columns:
        flags += (df["debt_equity"] > 3.0).astype(int)

    fraud_label = pd.cut(flags, bins=[-1, 0, 1, 10], labels=[0, 1, 2]).astype(int)

    feature_cols = [
        "ofs_pct", "net_margin", "promoter_stake_pre", "pat_cagr_3y",
        "debt_equity", "revenue_cagr_3y", "ebitda_margin",
        "interest_coverage", "current_ratio", "fresh_issue_pct",
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].fillna(df[available].median())

    model = DecisionTreeClassifier(
        max_depth=4, min_samples_leaf=3, random_state=RANDOM_SEED
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    scores = cross_val_score(model, X, fraud_label, cv=cv, scoring="f1_macro")
    print(f"[M7] CV Macro F1: {scores.round(3)} | Mean: {scores.mean():.3f}")

    model.fit(X, fraud_label)

    rules = [
        {"rule_id": "FR001", "feature": "net_margin", "threshold": -15,
         "severity": "high", "description": "Sustained losses (net margin < -15%)"},
        {"rule_id": "FR002", "feature": "ofs_pct", "threshold": 70,
         "severity": "high", "description": "High OFS proportion (>70%) - primary promoter exit signal"},
        {"rule_id": "FR003", "feature": "promoter_stake_pre", "threshold": 30,
         "severity": "medium", "description": "Low promoter skin-in-game (stake < 30%)"},
        {"rule_id": "FR004", "feature": "pat_cagr_3y", "threshold": -30,
         "severity": "medium", "description": "Accelerating profit decline (PAT CAGR < -30%)"},
        {"rule_id": "FR005", "feature": "debt_equity", "threshold": 3.0,
         "severity": "medium", "description": "Extreme leverage (D/E > 3x)"},
    ]

    joblib.dump({"model": model, "features": available, "rules": rules},
                MODELS_DIR / "fraud_model.pkl")
    print(f"[M7] Saved -> {MODELS_DIR / 'fraud_model.pkl'}")
    return model


# --- M5: Recommendation Engine (Score Aggregation) ---

def build_m5_recommendation(df: pd.DataFrame):
    """M5 is a weighted ranking config - no ML training needed."""
    print("\n[M5] Building Recommendation Engine config...")
    weights = {
        "financial_score": 0.30,
        "sentiment_score": 0.20,
        "risk_score_inv": 0.30,
        "subscription_score": 0.20,
    }
    joblib.dump(weights, MODELS_DIR / "recommendation_model.pkl")
    print(f"[M5] Saved weights -> {MODELS_DIR / 'recommendation_model.pkl'}")
    return weights


# --- Main ---

def main(target: str = "all"):
    master_csv = DATA_DIR / "ipo_master.csv"
    if not master_csv.exists():
        print(f"[ERROR] {master_csv} not found. Run feature_engineering.py first.")
        return

    df = pd.read_csv(master_csv)
    print(f"[INFO] Loaded {len(df)} rows from ipo_master.csv")

    if target in ("all", "m3"):
        train_m3_financial(df)
    if target in ("all", "m2"):
        build_m2_sentiment(df)
    if target in ("all", "m8"):
        train_m8_peers(df)
    if target in ("all", "m1"):
        train_m1_risk(df)
    if target in ("all", "m6"):
        train_m6_subscription(df)
    if target in ("all", "m4"):
        train_m4_listing_price(df)
    if target in ("all", "m7"):
        train_m7_fraud(df)
    if target in ("all", "m5"):
        build_m5_recommendation(df)

    print("\n[DONE] All models trained and saved.")
    print(f"Model files in: {MODELS_DIR}")
    for f in sorted(MODELS_DIR.glob("*.pkl")):
        print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="all",
                        choices=["all", "m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"])
    args = parser.parse_args()
    main(args.model)
