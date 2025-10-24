import yfinance as yf
import pandas as pd
import numpy as np
import json

# --- Hilfsfunktionen für einfache Pattern-Erkennung ---

def detect_double_top_bottom(series):
    """Sehr einfache Erkennung von Double Top / Bottom"""
    if len(series) < 5:
        return None
    mid = len(series)//2
    first = series[:mid].max()
    second = series[mid:].max()
    if abs(first - second)/first < 0.01:
        return "Double Top"
    first_min = series[:mid].min()
    second_min = series[mid:].min()
    if abs(first_min - second_min)/first_min < 0.01:
        return "Double Bottom"
    return None

def detect_trend(series):
    """Einfacher Trend Indikator"""
    if series[-1] > series[0]:
        return "Aufwärtstrend"
    elif series[-1] < series[0]:
        return "Abwärtstrend"
    else:
        return None

# --- Assets laden ---
tickers_file = "prognose.txt"
tickers = []
with open(tickers_file, "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            tickers.append(line)

# --- Daten abrufen ---
results = []

for ticker in tickers:
    try:
        yf_ticker = ticker
        # Anpassung für Forex (Yahoo Finance hängt =X hinten)
        if ticker.isalpha() and len(ticker) == 6:  # z.B. EURUSD
            yf_ticker = ticker[:3] + ticker[3:] + "=X"
        df = yf.download(yf_ticker, period="7d", interval="1h", progress=False)
        if df.empty:
            print(f"Keine Daten für {ticker}")
            continue

        close = df['Close']
        pattern = detect_double_top_bottom(close)
        trend = detect_trend(close)

        results.append({
            "ticker": ticker,
            "pattern": pattern if pattern else trend,
            "confidence": 0.95 if pattern else 0.85
        })

    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

# Ergebnisse als JSON speichern für prognose_to_discord.py
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Analyse abgeschlossen. Ergebnisse in results.json gespeichert.")
