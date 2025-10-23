import json
import yfinance as yf
from datetime import datetime
import pytz
import time
import os

# === Zeitzonen ===
TZ_BERLIN = pytz.timezone("Europe/Berlin")
now_berlin = datetime.now(TZ_BERLIN)

# === Handelszeiten prüfen ===
def is_market_open(market: str) -> bool:
    weekday = now_berlin.weekday()
    if weekday >= 5:  # Wochenende
        return False
    if market == "XETRA":
        return 9 <= now_berlin.hour < 17 or (now_berlin.hour == 17 and now_berlin.minute <= 30)
    elif market == "NYSE":
        from datetime import timezone, timedelta
        now_ny = datetime.now(pytz.timezone("America/New_York"))
        return (now_ny.hour > 9 or (now_ny.hour == 9 and now_ny.minute >= 30)) and now_ny.hour < 16
    elif market == "TOKYO":
        now_tokyo = datetime.now(pytz.timezone("Asia/Tokyo"))
        return 9 <= now_tokyo.hour < 15
    elif market == "HONGKONG":
        now_hk = datetime.now(pytz.timezone("Asia/Hong_Kong"))
        return (now_hk.hour > 9 or (now_hk.hour == 9 and now_hk.minute >= 30)) and now_hk.hour < 16
    return False

# === Börse anhand Tickers erkennen ===
def detect_market(ticker_symbol: str) -> str:
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol.endswith(".DE") or ticker_symbol.endswith(".F"):
        return "XETRA"
    elif ticker_symbol.endswith(".T"):
        return "TOKYO"
    elif ticker_symbol.endswith(".HK"):
        return "HONGKONG"
    else:
        return "NYSE"

# === Ticker einlesen ===
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f.readlines() if line.strip()]

output_data = []

print(f"🇩🇪 Berlin: {now_berlin.strftime('%Y-%m-%d %H:%M:%S')}\n")

for ticker_symbol in tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        market = detect_market(ticker_symbol)
        market_open = is_market_open(market)

        # Live oder Tagesdaten
        if market_open:
            interval = "15m" if market == "XETRA" else "5m" if market in ["NYSE","HONGKONG"] else "10m"
            data = ticker.history(period="1d", interval=interval)
        else:
            data = ticker.history(period="2d")

        price = float(data["Close"].iloc[-1]) if not data.empty else None
        previous_close = ticker.info.get("previousClose", None)

        output_data.append({
            "ticker": ticker_symbol,
            "market": market,
            "price": price,
            "previous_close": previous_close
        })

        print(f"✅ {ticker_symbol} ({market}): {price} (Prev: {previous_close})")
        time.sleep(0.4)

    except Exception as e:
        print(f"⚠️ Fehler bei {ticker_symbol}: {e}")
        output_data.append({"ticker": ticker_symbol, "market": None, "price": None, "previous_close": None})

# === Alte Daten vergleichen (robust) ===
old_data = None
if os.path.exists("monitor_output.json"):
    with open("monitor_output.json", "r") as f:
        try:
            old_data = json.load(f)
        except json.JSONDecodeError:
            old_data = None

def simplify(data):
    simplified = []
    for row in data:
        simplified.append({
            "ticker": row.get("ticker"),
            "price": round(row.get("price",0) or 0,2),
            "previous_close": round(row.get("previous_close",0) or 0,2)
        })
    return simplified

# Änderungen erkennen
if old_data is not None and simplify(old_data) == simplify(output_data):
    print("⚠️ Keine Änderungen gegenüber dem letzten Lauf erkannt.")
    with open("no_change.flag", "w") as f:
        f.write("no change")
else:
    if os.path.exists("no_change.flag"):
        os.remove("no_change.flag")
    print("✅ Neue Daten erkannt und gespeichert.")

# JSON speichern
with open("monitor_output.json", "w") as f:
    json.dump(output_data, f, indent=4)

print("\n📈 monitor_output.json erfolgreich aktualisiert!")
