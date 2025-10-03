import yfinance as yf
import json
import time
import pandas as pd

# Ticker aus Datei laden
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

data_list = []

# Kurs und Veränderung abrufen
for ticker in tickers:
    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice")
        prev_close = info.get("regularMarketPreviousClose")
        if price is not None and prev_close is not None:
            change_pct = ((price - prev_close) / prev_close) * 100
            data_list.append({
                "ticker": ticker,
                "price": round(price, 2),
                "change_pct": round(change_pct, 2)
            })
        time.sleep(0.5)  # Rate-Limit Schutz
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

# DataFrame erstellen für Sortierung
df = pd.DataFrame(data_list)

# Top 10 nach Performance
top_10 = df.sort_values(by="change_pct", ascending=False).head(10)

# Bottom 5 nach Performance
bottom_5 = df.sort_values(by="change_pct", ascending=True).head(5)

# Ergebnis flach zusammenführen für Numerics
result = {}
for _, row in pd.concat([top_10, bottom_5]).iterrows():
    result[row["ticker"]] = row["price"]

# JSON speichern
with open("monitor_output.json", "w") as f:
    json.dump(result, f, indent=2)

print("monitor_output.json (flach für Numerics) wurde erfolgreich erstellt!")
