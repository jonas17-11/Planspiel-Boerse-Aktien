import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 🔹 Assets laden (aus prognose.txt)
def load_assets(filename="prognose.txt"):
    assets = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            symbol = line.split()[0]
            assets.append(symbol)
    return assets

ASSET_NAMES = {}
with open("prognose.txt", "r", encoding="utf-8") as f:
    for line in f:
        if "#" in line and not line.strip().startswith("#"):
            parts = line.split("#")
            ticker = parts[0].strip()
            name = parts[1].strip()
            ASSET_NAMES[ticker] = name
        elif line.strip() and not line.startswith("#"):
            ASSET_NAMES[line.strip()] = line.strip()

assets = load_assets()

# 🔹 Kursdaten abrufen
def fetch_data(ticker, period="1mo", interval="1h"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

# 🔹 Musteranalyse (Pattern Detection)
def analyze_pattern(df):
    if df is None or len(df) < 10:
        return None, 0

    df["Change"] = df["Close"].pct_change()
    df["SMA5"] = df["Close"].rolling(5).mean()
    df["SMA20"] = df["Close"].rolling(20).mean()

    recent = df.iloc[-1]
    prev = df.iloc[-5:-1]

    pattern = "Seitwärtsbewegung"
    confidence = 50

    if recent["Close"] > recent["SMA20"] and all(prev["Close"] < prev["SMA20"]):
        pattern = "Trendwende nach oben"
        confidence = 85
    elif recent["Close"] < recent["SMA20"] and all(prev["Close"] > prev["SMA20"]):
        pattern = "Trendwende nach unten"
        confidence = 85
    elif df["Change"].iloc[-5:].mean() > 0.01:
        pattern = "Starker Aufwärtstrend"
        confidence = 90
    elif df["Change"].iloc[-5:].mean() < -0.01:
        pattern = "Starker Abwärtstrend"
        confidence = 90
    elif abs(df["Change"].iloc[-5:].mean()) < 0.002:
        pattern = "Seitwärtsbewegung"
        confidence = 60

    return pattern, confidence

# 🔹 Gesamtanalyse
def get_analysis():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        if df is None or len(df) < 10:
            continue

        pattern, confidence = analyze_pattern(df)
        if pattern:
            results.append({
                "ticker": ticker,
                "name": ASSET_NAMES.get(ticker, ticker),
                "pattern": pattern,
                "confidence": confidence,
                "change": (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100,
                "df": df
            })
    return results
