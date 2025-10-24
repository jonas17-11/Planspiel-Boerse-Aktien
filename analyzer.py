import yfinance as yf
import numpy as np
import datetime

def analyze_trend(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1h", progress=False)
        if len(data) < 3:
            return f"{symbol}: ⚠️ Nicht genug Daten"

        closes = data['Close'].values[-10:]
        trend = np.polyfit(range(len(closes)), closes, 1)[0]

        if trend > 0:
            direction = "📈 Steigender Trend erkannt"
        elif trend < 0:
            direction = "📉 Fallender Trend erkannt"
        else:
            direction = "➖ Seitwärtsbewegung"

        change = ((closes[-1] - closes[0]) / closes[0]) * 100
        confidence = abs(trend) / np.mean(closes) * 10000
        prognosis = "🔮 Wahrscheinlichkeit: "
        if confidence > 5:
            prognosis += "Hoch"
        elif confidence > 2:
            prognosis += "Mittel"
        else:
            prognosis += "Gering"

        return f"{symbol}: {direction} ({change:.2f}% in 10h) | {prognosis}"

    except Exception as e:
        return f"{symbol}: ❌ Fehler – {str(e)}"


def run_analysis():
    with open("data/prognose.txt", "r", encoding="utf-8") as f:
        symbols = [line.strip().split("#")[0].strip() for line in f if line.strip() and not line.startswith("#")]

    report = [f"📊 **Automatische Marktanalyse** ({datetime.datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr)\n"]
    for sym in symbols:
        report.append(analyze_trend(sym))

    return "\n".join(report)
