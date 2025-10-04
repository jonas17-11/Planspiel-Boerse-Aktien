import yfinance as yf
import json
from datetime import datetime

# Ticker aus Datei laden
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

data_list = []

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")  # wir brauchen Vortag + heute
        if len(hist) < 2:
            print(f"⚠️ Nicht genügend Daten für {ticker}")
            continue

        previous_close = hist["Close"].iloc[-2]
        current_price = hist["Close"].iloc[-1]
        change_percent = ((current_price - previous_close) / previous_close) * 100

        data_list.append({
            "ticker": ticker,
            "price": round(current_price, 2),
            "previous_close": round(previous_close, 2),
            "change_percent": round(change_percent, 2)
        })
    except Exception as e:
        print(f"❌ Fehler bei {ticker}: {e}")

# Ergebnisse speichern
output = {
    "timestamp": datetime.utcnow().isoformat(),
    "data": data_list
}

with open("monitor_output.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)

print(f"✅ {len(data_list)} Aktien aktualisiert und in monitor_output.json gespeichert.")
