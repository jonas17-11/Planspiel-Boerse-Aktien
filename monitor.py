import yfinance as yf
import pandas as pd
import json
from datetime import datetime

# ---- Aktienliste aus tickers.txt einlesen ----
tickers_file = "tickers.txt"
with open(tickers_file, "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

print(f"Es werden {len(tickers)} Ticker verarbeitet...")

# ---- Kurse abrufen ----
data = []
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d", interval="1m")
        if hist.empty:
            continue
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        change_percent = ((end_price - start_price) / start_price) * 100
        data.append({"ticker": ticker, "change_percent": round(change_percent, 2)})
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")

if not data:
    print("Keine Kursdaten abgerufen. JSON wird nicht erstellt.")
    exit()

# ---- Top 10 / Bottom 5 ----
df = pd.DataFrame(data)
top10_list = df.nlargest(10, "change_percent").to_dict(orient="records")
bottom5_list = df.nsmallest(5, "change_percent").to_dict(orient="records")

# ---- JSON speichern ----
output_data = {
    "top10": top10_list,
    "bottom5": bottom5_list,
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

with open("monitor_output.json", "w") as f:
    json.dump(output_data, f, indent=2)

print("monitor_output.json erfolgreich aktualisiert!")
