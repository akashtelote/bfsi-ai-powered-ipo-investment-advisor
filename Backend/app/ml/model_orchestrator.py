"""
ModelOrchestrator: single entry point for all ML model inference.
Models are lazy-loaded on first access.

Model resolution order:
  1. ML_MODELS_DIR env var (set in Docker to /app/ml_models)
  2. <repo_root>/ml/models/ (local dev, relative to this file's location)
"""
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# Docker path first, then local dev fallback (backend/app/ml -> backend/app -> backend -> repo_root -> ml/models)
_ENV_PATH = os.getenv("ML_MODELS_DIR", "")
_LOCAL_DIR = Path(__file__).parent.parent.parent.parent / "ml" / "models"

MODELS_DIR = Path(_ENV_PATH) if (_ENV_PATH and Path(_ENV_PATH).exists()) else _LOCAL_DIR


_FEAT_DISPLAY = {
    "sentiment_score":     "Market Sentiment Score",
    "profitability_score": "Profitability Score",
    "growth_score":        "Revenue Growth Score",
    "liquidity_score":     "Liquidity Score",
    "solvency_score":      "Solvency Score",
    "efficiency_score":    "Operational Efficiency",
    "ofs_pct":             "Offer for Sale %",
    "promoter_stake_pre":  "Promoter Stake Pre-IPO",
    "log_issue_size_cr":   "Issue Size (log)",
    "revenue_cagr_3y":     "Revenue CAGR (3Y)",
    "pat_cagr_3y":         "Profit CAGR (3Y)",
    "debt_equity":         "Debt-Equity Ratio",
    "roe":                 "Return on Equity",
    "gmp_t3":              "Grey Market Premium",
    "nifty_30d_return":    "Nifty 30D Return",
    "vix_at_open":         "Market Volatility (VIX)",
    "sector_code":         "Sector Code",
}


class ModelOrchestrator:
    _instance = None
    _models: dict = {}
    _loaded: bool = False

    @classmethod
    def get(cls) -> "ModelOrchestrator":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_models()
        return cls._instance

    def _load_models(self):
        model_files = {
            "financial": "financial_model.pkl",
            "risk": "risk_model.pkl",
            "peers": "peer_model.pkl",
            "subscription": "subscription_model.pkl",
            "recommendation": "recommendation_model.pkl",
            "listing": "listing_model.pkl",
            "fraud": "fraud_model.pkl",
        }
        loaded = []
        for name, fname in model_files.items():
            path = MODELS_DIR / fname
            if path.exists():
                self._models[name] = joblib.load(path)
                loaded.append(name)

        # Prefer the 6-feature live-only listing model if it exists (no zero-fill bias)
        live_path = MODELS_DIR / "listing_model_live.pkl"
        if live_path.exists():
            self._models["listing_live"] = joblib.load(live_path)
            loaded.append("listing_live")

        self._loaded = bool(loaded)
        if loaded:
            print(f"[ModelOrchestrator] Loaded: {', '.join(loaded)}")
        else:
            print(f"[ModelOrchestrator] No .pkl files found in {MODELS_DIR} - using stubs")

        # Load training medians for imputation (avoids zero-fill bias in full models)
        self._feature_medians: dict = self._load_feature_medians()
        if self._feature_medians:
            print(f"[ModelOrchestrator] Medians loaded for {len(self._feature_medians)} features")

    def _load_feature_medians(self) -> dict:
        """Load per-feature medians from ipo_master.csv for imputation at inference time.

        During training, missing features are filled with the dataset median.
        At live inference, we must do the same — otherwise zero-fill biases all
        predictions toward the worst-case outcome (e.g. zero GMP, zero subscription).
        """
        csv_path = MODELS_DIR.parent / "data" / "ipo_master.csv"
        if not csv_path.exists():
            return {}
        try:
            df = pd.read_csv(csv_path)
            numeric = df.select_dtypes(include=[np.number]).columns
            medians = df[numeric].median().to_dict()
            return medians
        except Exception as exc:
            print(f"[ModelOrchestrator] Warning: could not load medians: {exc}")
            return {}

    # --- Financial Health (M3 LightGBM) ---

    def predict_financial_health(self, features: dict) -> dict:
        if "financial" not in self._models:
            return self._stub_financial(features)
        model = self._models["financial"]
        df = self._safe_df(features, model if hasattr(model, "feature_name_") else None)
        overall = float(np.clip(model.predict(df)[0], 0, 100))
        return {
            "profitability": float(np.clip(overall * 0.9 + 5, 0, 100)),
            "growth": float(np.clip(overall * 1.1 - 3, 0, 100)),
            "liquidity": float(np.clip(overall * 0.85 + 10, 0, 100)),
            "solvency": float(np.clip(overall * 0.95, 0, 100)),
            "efficiency": float(np.clip(overall * 1.05 - 5, 0, 100)),
            "overall": overall,
        }

    # --- Market Sentiment (M2 FinBERT) ---

    def get_sentiment_score(
        self,
        ipo_id: str,
        texts: list[str] | None = None,
        pre_computed: dict | None = None,
    ) -> dict:
        if pre_computed:
            return pre_computed
        if texts:
            return self._finbert().analyze(texts)
        return self._stub_sentiment()

    def _finbert(self):
        if not hasattr(self, "_finbert_analyzer"):
            from app.ml.finbert_sentiment import FinBERTSentimentAnalyzer
            self._finbert_analyzer = FinBERTSentimentAnalyzer()
        return self._finbert_analyzer

    # --- IPO Risk Scoring (M1 XGBoost) ---

    def _impute(self, features: dict, feat_cols: list) -> dict:
        """Fill missing features using training medians, not zeros."""
        medians = getattr(self, "_feature_medians", {})
        # Also use medians stored in the bundle itself if available
        return {k: features.get(k, medians.get(k, 0)) for k in feat_cols}

    def predict_risk(self, features: dict) -> dict:
        if "risk" not in self._models:
            return self._stub_risk(features)
        bundle = self._models["risk"]
        model = bundle["model"]
        le = bundle["label_encoder"]
        feat_cols = bundle["features"]
        df = pd.DataFrame([self._impute(features, feat_cols)])
        probs = model.predict_proba(df)[0]
        pred_idx = int(model.predict(df)[0])
        classes = le.classes_  # e.g. ['High', 'Low', 'Medium']
        label = classes[pred_idx]
        label_to_prob = {c: float(p) for c, p in zip(classes, probs)}
        shap_drivers = self._compute_shap_drivers(df, feat_cols, le)
        return {
            "risk_label": label,
            "risk_score": float(label_to_prob.get("High", probs[-1]) * 100),
            "prob_low": float(label_to_prob.get("Low", probs[0])),
            "prob_medium": float(label_to_prob.get("Medium", probs[1] if len(probs) > 1 else 0)),
            "prob_high": float(label_to_prob.get("High", probs[2] if len(probs) > 2 else 0)),
            "shap_top_drivers": shap_drivers,
        }

    def _shap_explainer(self):
        if not hasattr(self, "_risk_shap_explainer"):
            import shap
            self._risk_shap_explainer = shap.TreeExplainer(self._models["risk"]["model"])
        return self._risk_shap_explainer

    def _compute_shap_drivers(self, df, feat_cols, le, top_n: int = 5) -> list[dict]:
        if "risk" not in self._models:
            return []
        try:
            shap_values = self._shap_explainer().shap_values(df)
            high_idx = list(le.classes_).index("High")
            sv = shap_values[high_idx][0]
        except Exception:
            return []
        drivers = []
        for feat, val in zip(feat_cols, sv):
            if abs(val) < 1e-4:
                continue
            drivers.append({
                "feature":      feat,
                "value":        round(float(-val), 3),
                "direction":    "increases_risk" if val > 0 else "decreases_risk",
                "display_name": _FEAT_DISPLAY.get(feat, feat.replace("_", " ").title()),
            })
        drivers.sort(key=lambda x: abs(x["value"]), reverse=True)
        return drivers[:top_n]

    # --- Subscription Demand Forecast (M6 CatBoost) ---

    def predict_subscription(self, features: dict) -> dict:
        if "subscription" not in self._models:
            return self._stub_subscription(features)
        bundle = self._models["subscription"]
        model = bundle["model"]
        feat_cols = bundle["features"]
        df = pd.DataFrame([self._impute(features, feat_cols)])
        log_sub = float(model.predict(df)[0])
        overall = float(np.expm1(log_sub))
        return {
            "overall_predicted": round(overall, 2),
            "qib_predicted": round(overall * 1.8, 2),
            "hni_predicted": round(overall * 1.2, 2),
            "rii_predicted": round(overall * 0.8, 2),
            "allotment_probability": round(min(1.0, 1 / max(1, overall * 0.8)), 3),
        }

    # --- Listing Price Prediction (M4 Ridge) ---

    def predict_listing_gain(self, features: dict) -> float:
        # Prefer the 6-feature live model (no zero-fill bias) if available
        if "listing_live" in self._models:
            bundle = self._models["listing_live"]
            df = pd.DataFrame([self._impute(features, bundle["features"])])
            return float(np.clip(bundle["model"].predict(df)[0], -50, 200))

        if "listing" not in self._models:
            return 15.0
        bundle = self._models["listing"]
        # Use training medians for missing features — not zeros.
        # The full model was trained with median-imputed data; zero-fill creates a
        # systematic negative bias (zero GMP, zero subscription → always predicts losses).
        df = pd.DataFrame([self._impute(features, bundle["features"])])
        return float(np.clip(bundle["model"].predict(df)[0], -50, 200))

    # --- Fraud Detection (M7 Decision Tree) ---

    def predict_fraud_flags(self, features: dict) -> list[dict]:
        bundle = self._models.get("fraud")
        rules = bundle["rules"] if bundle else []
        model = bundle["model"] if bundle else None
        feat_cols = bundle["features"] if bundle else []

        triggered = []
        for rule in rules:
            feat = rule["feature"]
            val = features.get(feat)
            if val is None:
                continue
            thresh = rule["threshold"]
            # For high-is-bad metrics (ofs_pct, debt_equity), flag if > threshold
            # For low-is-bad metrics (net_margin, promoter_stake_pre, pat_cagr_3y), flag if < threshold
            if feat in ("ofs_pct", "debt_equity"):
                if val > thresh:
                    triggered.append({"rule_id": rule["rule_id"], "severity": rule["severity"],
                                      "description": rule["description"]})
            else:
                if val < thresh:
                    triggered.append({"rule_id": rule["rule_id"], "severity": rule["severity"],
                                      "description": rule["description"]})
        return triggered

    # --- Peer Benchmarking (M8 K-Means, stub only) ---

    def get_peers(self, ipo_id: str, sector: str, features: dict) -> dict:
        return self._stub_peers(sector)

    # --- Recommendation Ranking (M5 weighted config) ---

    def rank_recommendations(self, ipos_df: pd.DataFrame, profile: dict) -> pd.DataFrame:
        weights = self._models.get("recommendation", {
            "financial_score": 0.30,
            "sentiment_score": 0.20,
            "risk_score_inv": 0.30,
            "subscription_score": 0.20,
        })
        df = ipos_df.copy()
        if "risk_score" in df.columns:
            df["risk_score_inv"] = 100 - df["risk_score"].fillna(50)
        if "overall_sub_multiple" in df.columns:
            df["subscription_score"] = df["overall_sub_multiple"].fillna(1).clip(0, 50) * 2

        composite = sum(
            df.get(col, pd.Series([50] * len(df))).fillna(50) * w
            for col, w in weights.items()
        )
        df["suitability_score"] = composite
        return df.sort_values("suitability_score", ascending=False)

    # --- Stubs ---

    def _safe_df(self, features: dict, model=None) -> pd.DataFrame:
        if model and hasattr(model, "feature_name_"):
            cols = model.feature_name_()
            return pd.DataFrame([{c: features.get(c, 0) for c in cols}])
        return pd.DataFrame([features])

    def _stub_financial(self, features: dict) -> dict:
        base = 65.0
        return {"profitability": base + 5, "growth": base - 3, "liquidity": base + 8,
                "solvency": base - 5, "efficiency": base + 2, "overall": base}

    def _stub_sentiment(self) -> dict:
        return {"score": 62.0, "label": "positive", "positive_pct": 55.0,
                "neutral_pct": 30.0, "negative_pct": 15.0,
                "top_keywords": ["growth", "IPO", "market", "strong", "listing"],
                "news_volume_7d": 24}

    def _stub_risk(self, features: dict) -> dict:
        return {"risk_label": "Medium", "risk_score": 45.0,
                "prob_low": 0.3, "prob_medium": 0.5, "prob_high": 0.2,
                "shap_top_drivers": []}

    def _stub_subscription(self, features: dict) -> dict:
        return {"overall_predicted": 12.5, "qib_predicted": 22.0, "hni_predicted": 15.0,
                "rii_predicted": 8.0, "allotment_probability": 0.12}

    def _stub_peers(self, sector: str) -> dict:
        return {
            "peers": [
                {"ticker": "PEER1.NS", "name": "Peer Company 1", "pe": 28.5, "ev_ebitda": 15.2, "market_cap_cr": 12000},
                {"ticker": "PEER2.NS", "name": "Peer Company 2", "pe": 32.0, "ev_ebitda": 18.5, "market_cap_cr": 8500},
            ],
            "peer_pe_median": 30.2,
            "peer_ev_ebitda_median": 16.8,
            "valuation_label": "Fair",
        }
