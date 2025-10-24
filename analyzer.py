import yfinance as yf
import numpy as np
import datetime
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "prognose.txt")

# --- Hilfsfunktionen für Pattern-Erkennung mit Confidence ---
def pattern_confidence(prices, pattern_func):
    """Gibt einen Wert 0-1 zurück, wie wahrscheinlich das Pattern ist"""
    if pattern_func(prices):
        # Beispiel: Trendstärke und Konsolidierung → höhere Wahrscheinlichkeit
        trend_strength = abs(prices[-1] - prices[0]) / prices[0]
        volatility = np.std(prices) / np.mean(prices)
        confidence = trend_strength / (volatility + 0.01)
        return confidence
    return 0

# Beispiel Pattern-Funktionen
def is_bullish_flag(prices):
    if len(prices) < 10: return False
    return prices[-1] > prices[0] and np.std(prices[-5:]) < 0.01*np.mean(prices[-5:])
def is_bearish_flag(prices):
    if len(prices) < 10: return False
    return prices[-1] < prices[0] and np.std(prices[-5:]) < 0.01*np.mean(prices[-5:])
# ... weitere Pattern-Funktionen wie Double Top, Double Bottom, etc. bleiben gleich ...

# --- Analyse eines Symbols ---
def analyze_pattern(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1h", progress=False)
        if len(data) < 10: return None
        closes = data['Close'].values[-10:]

        patterns = []
        confidences = []

        funcs = [
            ("Bullish Flag", is_bullish_flag),
            ("Bearish Flag", is_bearish_flag),
            ("Double Top", is_double_top),
            ("Double Bottom", is_double_bottom),
            ("Head and Shoulders", is_head_and_shoulders),
            ("Inverse Head and Shoulders", is_inverse_head_and_shoulders),
            ("Rising Wedge", is_rising_wedge),
            ("Falling Wedge", is_falling_wedge),
            ("Triple Top", is_triple_top),
            ("Triple Bottom", is_triple_bottom),
            ("Cup and Handle", is_cup_and_handle),
            ("Pennant", is_pennant)
        ]

        for name, func in funcs:
            conf = pattern_confidence(closes, func)
            if conf > 0:
                patterns.append(name)
                confidences.append(conf)

        if not patterns:
            return None

        # Gesamt-Confidence als Durchschnitt der einzelnen Patterns
        total_confidence = sum(confidences) / len(confidences)

        # Richtung bestimmen
        trend_strength = closes[-1] - closes[0]

        return {
            "symbol": symbol,
            "patterns": patterns,
            "trend_strength": trend_strength,
            "confidence": total_confidence
        }

    except Exception:
        return None

# --- Top-Picks nach Wahrscheinlichkeit ---
def run_analysis_patterns():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        symbols = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for sym in symbols:
        res = analyze_pattern(sym)
        if res:
            results.append(res)

    # Aufwärts: höchste Confidence
    results_sorted_up = sorted([r for r in results if r['trend_strength'] > 0], key=lambda x: x['confidence'], reverse=True)[:10]
    # Abwärts: höchste Confidence
    results_sorted_down = sorted([r for r in results if r['trend_strength'] < 0], key=lambda x: x['confidence'], reverse=True)[:10]

    report = [f"📊 **Top-Picks Chart-Pattern Analyse (höchste Wahrscheinlichkeit)** ({datetime.datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr)\n"]

    report.append("\n📈 **Top 10 Aufwärtspatterns:**")
    for r in results_sorted_up:
        report.append(f"{r['symbol']}: {', '.join(r['patterns'])} | Wahrscheinlichkeit: {r['confidence']:.2f}")

    report.append("\n📉 **Top 10 Abwärtspatterns:**")
    for r in results_sorted_down:
        report.append(f"{r['symbol']}: {', '.join(r['patterns'])} | Wahrscheinlichkeit: {r['confidence']:.2f}")

    return "\n".join(report)
