import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

# --- Candlestick Pattern Erkennung ---
def detect_candlestick_patterns(df):
    patterns = []

    for i in range(1, len(df)):
        o, h, l, c = df["Open"].iloc[i], df["High"].iloc[i], df["Low"].iloc[i], df["Close"].iloc[i]
        prev_o, prev_c = df["Open"].iloc[i - 1], df["Close"].iloc[i - 1]

        body = abs(c - o)
        range_ = h - l
        upper_shadow = h - max(c, o)
        lower_shadow = min(c, o) - l

        pattern = None

        # Doji
        if body < 0.1 * range_:
            pattern = "Doji"

        # Hammer (bullish)
        elif lower_shadow > 2 * body and upper_shadow < body:
            if c > o:
                pattern = "Hammer"

        # Shooting Star (bearish)
        elif upper_shadow > 2 * body and lower_shadow < body:
            if c < o:
                pattern = "Shooting Star"

        # Bullish Engulfing
        elif c > o and prev_c < prev_o and c > prev_o and o < prev_c:
            pattern = "Bullish Engulfing"

        # Bearish Engulfing
        elif c < o and prev_c > prev_o and o > prev_c and c < prev_o:
            pattern = "Bearish Engulfing"

        patterns.append(pattern)

    df["Pattern"] = [None] + patterns
    return df


# --- Analyse und Prognose ---
def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="30d", interval="1h", progress=False)
        if df.empty:
            return None

        df = detect_candlestick_patterns(df)
        latest_pattern = df["Pattern"].dropna().iloc[-1] if df["Pattern"].dropna().any() else None

        if latest_pattern is None:
            return None

        # Simpler Prognoseansatz
        last_close = df["Close"].iloc[-1]
        if latest_pattern in ["Bullish Engulfing", "Hammer"]:
            forecast = last_close * 1.02
            trend = "steigend"
            confidence = 80
        elif latest_pattern in ["Bearish Engulfing", "Shooting Star"]:
            forecast = last_close * 0.98
            trend = "fallend"
            confidence = 80
        elif latest_pattern == "Doji":
            forecast = last_close
            trend = "neutral"
            confidence = 50
        else:
            forecast = last_close
            trend = "neutral"
            confidence = 50

        # Diagramm erstellen
        plt.figure(figsize=(6, 3))
        plt.plot(df.index, df["Close"], label="Echter Kurs", color="blue")
        plt.axvline(df.index[-1], color="gray", linestyle="--", alpha=0.5)
        plt.scatter(df.index[-1], last_close, color="green" if trend == "steigend" else "red", s=40, zorder=5)
        plt.plot([df.index[-1], df.index[-1] + timedelta(days=1)], [last_close, forecast],
                 color="red" if trend == "fallend" else "green", linestyle="--", label="Prognose")
        plt.title(f"{ticker} ({latest_pattern})")
        plt.legend()
        plt.tight_layout()

        os.makedirs("charts", exist_ok=True)
        chart_path = f"charts/{ticker.replace('/', '_')}.png"
        plt.savefig(chart_path)
        plt.close()

        return {
            "ticker": ticker,
            "pattern": latest_pattern,
            "trend": trend,
            "confidence": confidence,
            "forecast": forecast,
            "chart": chart_path,
            "last_close": last_close,
        }

    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None


# --- Hauptanalyse ---
def get_analysis():
    with open("prognose.txt", "r") as f:
        tickers = [line.split("#")[0].strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for ticker in tickers:
        res = analyze_ticker(ticker)
        if res:
            results.append(res)

    if not results:
        return None

    bullish = [r for r in results if r["trend"] == "steigend"]
    bearish = [r for r in results if r["trend"] == "fallend"]

    bullish_sorted = sorted(bullish, key=lambda x: x["confidence"], reverse=True)[:10]
    bearish_sorted = sorted(bearish, key=lambda x: x["confidence"], reverse=True)[:10]

    return bullish_sorted, bearish_sorted


if __name__ == "__main__":
    b, s = get_analysis()
    print("📈 Steigende Kandidaten:")
    for r in b:
        print(f"{r['ticker']}: {r['pattern']} ({r['confidence']}%)")

    print("\n📉 Fallende Kandidaten:")
    for r in s:
        print(f"{r['ticker']}: {r['pattern']} ({r['confidence']}%)")
