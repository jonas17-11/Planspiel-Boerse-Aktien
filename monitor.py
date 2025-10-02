import yfinance as yf
import json

# Tickers aus Datei einlesen
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f.readlines()]

results = []

# Kurse abrufen und prozentuale Veränderung berechnen
for ticker in tickers:
    try:
        data = yf.Ticker(ticker).history(period="1d", interval="5m")
        if not data.empty and len(data) > 1:
            last_price = data["Close"].iloc[-1]
            prev_price = data["Close"].iloc[-2]
            change = ((last_price - prev_price) / prev_price) * 100
            results.append({
                "ticker": ticker,
                "last_price": round(last_price, 2),
                "change_percent": round(change, 2)
            })
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

# Nach größtem Aufwärtspotenzial sortieren und Top 10 auswählen
top10 = sorted(results, key=lambda x: x["change_percent"], reverse=True)[:10]

# JSON-Datei speichern
with open("monitor_output.json", "w") as f:
    json.dump(top10, f, indent=2)

print("Fertig! Top 10 Ergebnisse in monitor_output.json gespeichert.")
