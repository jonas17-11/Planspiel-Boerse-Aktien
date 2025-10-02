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

# Top 10 beste Aktien
top10_best = sorted(results, key=lambda x: x["change_percent"], reverse=True)[:10]

# Top 5 schlechteste Aktien
top5_worst = sorted(results, key=lambda x: x["change_percent"])[:5]

# JSON speichern
output = {
    "top10_best": top10_best,
    "top5_worst": top5_worst
}
with open("monitor_output.json", "w") as f:
    json.dump(output, f, indent=2)

# GitHub Actions Log Ausgabe
def print_table(title, data):
    print(f"\n=== {title} ===")
    print(f"{'Ticker':<10}{'Price':<10}{'Change (%)':<12}")
    print("-" * 32)
    for item in data:
        print(f"{item['ticker']:<10}{item['last_price']:<10}{item['change_percent']:<12}")

print_table("Top 10 Beste", top10_best)
print_table("Top 5 Schlechteste", top5_worst)
