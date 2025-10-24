import yfinance as yf
import numpy as np
import datetime
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "prognose.txt")

# --- Hilfsfunktionen für Pattern-Erkennung ---
def pattern_confidence(prices, pattern_func):
    """Gibt einen Wert 0-1 zurück, wie wahrscheinlich das Pattern ist"""
    if pattern_func(prices):
        trend_strength = abs(prices[-1] - prices[0]) / prices[0]
        volatility = np.std(prices) / np.mean(prices)
        confidence = trend_strength / (volatility + 0.01)
        return confidence
    return 0

# --- Beispiel Pattern-Funktionen ---
def is_bullish_flag(prices):
    if len(prices) < 10: return False
    return prices[-1] > prices[0] and np.std(prices[-5:]) < 0.01*np.mean(prices[-5:])
def is_bearish_flag(prices):
    if len(prices) < 10: return False
    return prices[-1] < prices[0] and np.std(prices[-5:]) < 0.01*np.mean(prices[-5:])
def is_double_top(prices): return False
def is_double_bottom(prices): return False
def is_head_and_shoulders(prices): return False
def is_inverse_head_and_shoulders(prices): return False
def is_rising_wedge(prices): return False
def is_falling_wedge(prices): return False
def is_triple_top(prices): return False
def is_triple_bottom(prices): return False
def is_cup_and_handle(prices): return False
def is_pennant(prices): return False

PATTERNS = [
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

# --- Analyse eines Symbols ---
def analyze_pattern(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1h", progress=False)
        if len(data) < 10: return None
        closes = data['Close'].values[-10:]

        patterns_detected = []
        confidences = []

        for name, func in PATTERNS:
            conf = pattern_confidence(closes, func)
            if conf > 0:
                patterns_detected.append(name)
                confidences.append(conf)

        # Fallback: wenn kein Pattern erkannt, trotzdem Confidence basierend auf Trend
        if not patterns_detected:
            patterns_detected = ["No Pattern"]
            trend_strength = closes[-1] - closes[0]
            confidence = abs(trend_strength) / (np.std(closes)+0.01)
            confidences = [confidence]
        else:
            confidence = sum(confidences) / len(confidences)

        trend_strength = closes[-1] - closes[0]

        return {
            "symbol": symbol,
            "patterns": patterns_detected,
            "trend_strength": trend_strength,
            "confidence": confidence
        }
    except Exception:
        return None

# --- Top-Picks nach Wahrscheinlichkeit mit Fallback ---
def run_analysis_patterns():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        symbols = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for sym in symbols:
        res = analyze_pattern(sym)
        if res:
            results.append(res)

    # Aufwärts: sortiert nach Confidence
    results_up = sorted([r for r in results if r['trend_strength'] > 0], key=lambda x: x['confidence'], reverse=True)
    # Abwärts: sortiert nach Confidence
    results_down = sorted([r for r in results if r['trend_strength'] < 0], key=lambda x: x['confidence'], reverse=True)

    # Fallback: falls weniger als 10, fülle mit nächstbesten
    if len(results_up) < 10:
        fallback_up = sorted([r for r in results if r['trend_strength'] <= 0], key=lambda x: x['confidence'], reverse=True)
        results_up += fallback_up[:10 - len(results_up)]

    if len(results_down) < 10:
        fallback_down = sorted([r for r in results if r['trend_strength'] >= 0], key=lambda x: x['confidence'], reverse=True)
        results_down += fallback_down[:10 - len(results_down)]

    # Limit auf 10
    results_up = results_up[:10]
    results_down = results_down[:10]

    report = [f"📊 Top-Picks Chart-Pattern Analyse (höchste Wahrscheinlichkeit) ({datetime.datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr)"]
    report.append("\n📈 Top 10 Aufwärtspatterns:")
    for r in results_up:
        report.append(f"{r['symbol']}: {', '.join(r['patterns'])} | 🔮 {r['confidence']:.2f}")

    report.append("\n📉 Top 10 Abwärtspatterns:")
    for r in results_down:
        report.append(f"{r['symbol']}: {', '.join(r['patterns'])} | 🔮 {r['confidence']:.2f}")

    return "\n".join(report)
