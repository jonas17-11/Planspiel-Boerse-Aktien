import yfinance as yf
import numpy as np
import datetime
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "prognose.txt")

# --- Hilfsfunktionen für Pattern-Erkennung ---
def is_bullish_flag(prices):
    if len(prices) < 10:
        return False
    return prices[-1] > prices[0] and np.std(prices[-5:]) < 0.01 * np.mean(prices[-5:])

def is_bearish_flag(prices):
    if len(prices) < 10:
        return False
    return prices[-1] < prices[0] and np.std(prices[-5:]) < 0.01 * np.mean(prices[-5:])

def is_double_top(prices):
    if len(prices) < 10:
        return False
    peak1 = max(prices[:5])
    peak2 = max(prices[5:])
    return abs(peak1 - peak2)/peak1 < 0.02 and prices[-1] < peak2

def is_double_bottom(prices):
    if len(prices) < 10:
        return False
    low1 = min(prices[:5])
    low2 = min(prices[5:])
    return abs(low1 - low2)/low1 < 0.02 and prices[-1] > low2

def is_head_and_shoulders(prices):
    if len(prices) < 9:
        return False
    left = prices[0:3]
    head = prices[3:6]
    right = prices[6:9]
    return max(head) > max(left) and max(head) > max(right)

def is_inverse_head_and_shoulders(prices):
    if len(prices) < 9:
        return False
    left = prices[0:3]
    head = prices[3:6]
    right = prices[6:9]
    return min(head) < min(left) and min(head) < min(right)

def is_rising_wedge(prices):
    if len(prices) < 6:
        return False
    return prices[-1] > prices[0] and all(np.diff(prices) > 0)

def is_falling_wedge(prices):
    if len(prices) < 6:
        return False
    return prices[-1] < prices[0] and all(np.diff(prices) < 0)

def is_triple_top(prices):
    if len(prices) < 15:
        return False
    peaks = [max(prices[i:i+5]) for i in range(0, 15, 5)]
    return max(peaks) - min(peaks) < 0.02 * np.mean(peaks)

def is_triple_bottom(prices):
    if len(prices) < 15:
        return False
    lows = [min(prices[i:i+5]) for i in range(0, 15, 5)]
    return max(lows) - min(lows) < 0.02 * np.mean(lows)

def is_cup_and_handle(prices):
    if len(prices) < 10:
        return False
    cup = prices[:7]
    handle = prices[7:]
    return min(cup) < cup[0] and max(handle) < max(cup)

def is_pennant(prices):
    if len(prices) < 10:
        return False
    return abs(prices[-1] - prices[0]) < 0.02 * np.mean(prices) and np.std(prices) < 0.01 * np.mean(prices)

# --- Analysefunktion ---
def analyze_pattern(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1h", progress=False)
        if len(data) < 10:
            return None
        closes = data['Close'].values[-10:]
        patterns = []
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
            if func(closes):
                patterns.append(name)
        if not patterns:
            return None
        trend_strength = abs(closes[-1] - closes[0])/closes[0] * 100
        return {
            "symbol": symbol,
            "patterns": patterns,
            "trend_strength": trend_strength
        }
    except Exception:
        return None

def run_analysis_patterns():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        symbols = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for sym in symbols:
        res = analyze_pattern(sym)
        if res:
            results.append(res)

    results_sorted_up = sorted([r for r in results if r['trend_strength'] > 0], key=lambda x: x['trend_strength'], reverse=True)[:10]
    results_sorted_down = sorted([r for r in results if r['trend_strength'] < 0], key=lambda x: x['trend_strength'])[:10]

    report = [f"📊 **Top-Picks Chart-Pattern Analyse** ({datetime.datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr)\n"]
    report.append("\n📈 **Top 10 Aufwärtspatterns:**")
    for r in results_sorted_up:
        report.append(f"{r['symbol']}: {', '.join(r['patterns'])} | Trendstärke: {r['trend_strength']:.2f}%")
    report.append("\n📉 **Top 10 Abwärtspatterns:**")
    for r in results_sorted_down:
        report.append(f"{r['symbol']}: {', '.join(r['patterns'])} | Trendstärke: {r['trend_strength']:.2f}%")
    return "\n".join(report)
