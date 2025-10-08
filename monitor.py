import json
import yfinance as yf

# Lies die Ticker-Liste ein
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f.readlines() if line.strip()]

output_data = []

for ticker_symbol in tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.history(period="2d")  # Letzte 2 Tage für Preis + vorherigen Schlusskurs
        if info.empty or len(info) < 2:
            # Falls keine Daten, setze None
            price = None
            previous_close = None
        else:
            price = info['Close'][-1]
            previous_close = info['Close'][-2]

        output_data.append({
            "ticker": ticker_symbol,
            "price": price,
            "previous_close": previous_close
        })

    except Exception as e:
        # Falls ein Fehler beim Abrufen der Daten passiert
        print(f"Fehler bei {ticker_symbol}: {e}")
        output_data.append({
            "ticker": ticker_symbol,
            "price": None,
            "previous_close": None
        })

# Schreibe die Daten in monitor_output.json
with open("monitor_output.json", "w") as f:
    json.dump(output_data, f, indent=4)

print("monitor_output.json wurde erfolgreich aktualisiert!")
