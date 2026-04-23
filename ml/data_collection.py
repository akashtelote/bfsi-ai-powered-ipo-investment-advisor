"""
data_collection.py — Day 1 DS Track script
Downloads yfinance data (NIFTY50, VIX, peer stocks) and merges with manually
downloaded CSVs (Chittorgarh IPO master, NSE subscription data, Screener.in financials).

Usage:
    python ml/data_collection.py

Outputs (written to ml/data/):
    nifty_daily.csv      — NIFTY 50 daily OHLCV (2010–2024)
    vix_daily.csv        — India VIX daily (2014–2024)
    peer_stocks.csv      — ~200 listed peer stocks OHLCV + ratios
"""
import os
import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

START_DATE = "2010-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

# ─── NSE Sector ETFs and index proxies used as market features ────────────────
INDICES = {
    "NIFTY50": "^NSEI",
    "NIFTY_BANK": "^NSEBANK",
    "INDIA_VIX": "^INDIAVIX",
    "NIFTY_IT": "^CNXIT",
    "NIFTY_PHARMA": "^CNXPHARMA",
    "NIFTY_AUTO": "^CNXAUTO",
}

# Top listed peers across sectors (expand this list with real peers from screener.in)
PEER_TICKERS = [
    # IT
    "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    # BFSI
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    # Consumer
    "HINDUNILVR.NS", "NESTLEIND.NS", "DABUR.NS", "MARICO.NS",
    # Auto
    "MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS",
    # Pharma
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    # Energy
    "ONGC.NS", "BPCL.NS", "IOCL.NS",
    # Telecom
    "BHARTIARTL.NS", "IDEA.NS",
    # E-Commerce / New-Age
    "ZOMATO.NS", "NYKAA.NS", "PAYTM.NS", "DELHIVERY.NS",
]


def download_indices():
    print("[INFO] Downloading index/VIX data...")
    dfs = []
    for name, ticker in INDICES.items():
        try:
            df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True)
            if df.empty:
                print(f"[WARN] No data for {ticker}")
                continue
            df = df[["Close"]].rename(columns={"Close": name})
            dfs.append(df)
        except Exception as e:
            print(f"[WARN] Failed {ticker}: {e}")

    if dfs:
        merged = pd.concat(dfs, axis=1).sort_index()
        merged.to_csv(DATA_DIR / "market_indices.csv")
        print(f"[OK] market_indices.csv — {len(merged)} rows")
    return merged if dfs else pd.DataFrame()


def compute_market_features(indices_df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute rolling features that will be joined per IPO by open date."""
    df = indices_df.copy()
    if "NIFTY50" in df.columns:
        df["nifty_30d_return"] = df["NIFTY50"].pct_change(30) * 100
        df["nifty_5d_return"] = df["NIFTY50"].pct_change(5) * 100
    if "INDIA_VIX" in df.columns:
        df["vix_at_open"] = df["INDIA_VIX"]
    df.to_csv(DATA_DIR / "market_features.csv")
    print(f"[OK] market_features.csv — {len(df)} rows")
    return df


def download_peer_stocks():
    print(f"[INFO] Downloading {len(PEER_TICKERS)} peer stocks...")
    records = []
    for ticker in PEER_TICKERS:
        try:
            info = yf.Ticker(ticker).info
            records.append({
                "ticker": ticker,
                "name": info.get("shortName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap"),
                "pe_trailing": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "pb_ratio": info.get("priceToBook"),
                "roe": info.get("returnOnEquity"),
                "revenue": info.get("totalRevenue"),
                "net_income": info.get("netIncomeToCommon"),
                "debt_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
            })
        except Exception as e:
            print(f"[WARN] {ticker}: {e}")

    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "peer_stocks.csv", index=False)
    print(f"[OK] peer_stocks.csv — {len(df)} rows")
    return df


def merge_all_csvs():
    """
    Merge manually downloaded CSVs with yfinance data.
    Expected manual CSVs in ml/data/:
        ipo_list.csv        — from chittorgarh.com (company, dates, price band, listing price)
        subscription.csv    — from NSE archive (QIB/HNI/RII multiples)
        financials.csv      — from screener.in (revenue, PAT, D/E, ROE per company)
        gmp_data.csv        — from ipowatch.in (grey market premium)
    """
    required = ["ipo_list.csv", "subscription.csv", "financials.csv"]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        print(f"[WARN] Missing manual CSVs: {missing}")
        print("[INFO] Run the demo seed with available data for now.")
        return None

    ipo_df = pd.read_csv(DATA_DIR / "ipo_list.csv")
    sub_df = pd.read_csv(DATA_DIR / "subscription.csv")
    fin_df = pd.read_csv(DATA_DIR / "financials.csv")

    # Normalize company names for join
    for df in [ipo_df, sub_df, fin_df]:
        if "company_name" in df.columns:
            df["company_key"] = df["company_name"].str.lower().str.strip()

    master = ipo_df.merge(sub_df, on="company_key", how="left", suffixes=("", "_sub"))
    master = master.merge(fin_df, on="company_key", how="left", suffixes=("", "_fin"))

    if (DATA_DIR / "gmp_data.csv").exists():
        gmp_df = pd.read_csv(DATA_DIR / "gmp_data.csv")
        gmp_df["company_key"] = gmp_df["company_name"].str.lower().str.strip()
        master = master.merge(gmp_df[["company_key", "gmp_t3", "gmp_t1"]], on="company_key", how="left")

    master.to_csv(DATA_DIR / "ipo_master_raw.csv", index=False)
    print(f"[OK] ipo_master_raw.csv — {len(master)} rows, {len(master.columns)} columns")
    return master


if __name__ == "__main__":
    print("=" * 60)
    print("IPO Advisor — Data Collection Script")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print("=" * 60)

    indices = download_indices()
    if not indices.empty:
        compute_market_features(indices)

    download_peer_stocks()
    merge_all_csvs()

    print("\n[DONE] Data collection complete.")
    print(f"Output files in: {DATA_DIR}")
