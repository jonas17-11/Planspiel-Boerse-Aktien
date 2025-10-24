import yfinance as yf
import pandas as pd
import numpy as np

# Patterns (Beispiele, erweiterbar)
CHART_PATTERNS = [
    "Bullish Flag", "Bearish Flag", "Double Top", "Double Bottom",
    "Head and Shoulders", "Inverse Head and Shoulders", "Cup and Handle",
    "Rising Wedge", "Falling Wedge", "Triangle", "Rectangle"
]

# Einlesen der Assets
with open("prognose.txt", "r", encoding="utf-8") as f:
    ASSETS = [line.strip() for line in f if line.strip() and not line.startswith("#")]

def download_data(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1h", progress=False, auto_adjust=True)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"Fehler beim Download von {symbol}: {e}")
        return None

def detect_patterns(data):
    """
    Dummy-Funktion für Pattern-Erkennung.
    In echt kannst du hier komplexe Logik einfügen.
    Gibt zufällig 1-3 Patterns zurück + confidence.
    """
    num_patterns = np.random.randint(1, 4)
    patterns = list(np.random.choice(CHART_PATTERNS, size=num_patterns, replace=False))
    confidence = float(np.random.uniform(0.6, 0.99))  # Wahrscheinlichkeit 60%-99%
    return patterns, confidence

def run_analysis_patterns():
    results = []
    for symbol in ASSETS:
        data = download_data(symbol)
        if data is None:
            continue
        patterns, confidence = detect_patterns(data)
        results.append({
            "symbol": symbol,
            "patterns": patterns,
            "confidence": confidence
        })
    # Sortieren nach Wahrscheinlichkeit
    results_sorted = sorted(results, key=lambda x: x["confidence"], reverse=True)
    # Top 10 Aufwärts (hier Dummy, einfach confidence > 0.7)
    top_up = results_sorted[:10]
    # Top 10 Abwärts (restliche niedrigste confidence)
    bottom_down = results_sorted[-10:]
    return top_up, bottom_down
