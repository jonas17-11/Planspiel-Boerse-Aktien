import yfinance as yf
import json

# Tickers aus Datei einlesen
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f.readlines()]

results = []

# Kurse abrufen und einfache Potenzialberechnung
for ticker in tickers:
    try:
        data = yf.Ticker(ticker).history(period="1d", interval="5m")
        if not data.empty:
            last_price = data["Close"].iloc[-1]
            prev_price = data["Close"].iloc[-2] if len(data) > 1 else last_price
            change = ((last_price - prev_price) / prev_price) * 100
            results.append({
                "ticker": ticker,
                "last_price": round(last_price, 2),
                "change_percent": round(change, 2)
            })
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

# JSON-Ausgabe speichern
with open("monitor_output.json", "w") as f:
    json.dump(results, f, indent=2)

print("Fertig! Ergebnisse in monitor_output.json gespeichert.")
