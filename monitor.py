import yfinance as yf
import json
import time

# Ticker aus Datei laden
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

output = {}

for ticker in tickers:
    try:
        data = yf.Ticker(ticker).info
        price = data.get("regularMarketPrice")
        if price is not None:
            output[ticker] = round(price, 2)
        else:
            print(f"{ticker}: Kein Kurs gefunden")
        # Kurze Pause, um Rate-Limits zu vermeiden
        time.sleep(0.5)
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

# JSON im Key-Value Format speichern
with open("monitor_output.json", "w") as f:
    json.dump(output, f, indent=2)

print("monitor_output.json wurde erfolgreich erstellt!")
