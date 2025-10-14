import json
import yfinance as yf
from datetime import datetime
import pytz
import time

# === Zeitzonen ===
TZ_BERLIN = pytz.timezone("Europe/Berlin")
TZ_NEWYORK = pytz.timezone("America/New_York")
TZ_TOKYO = pytz.timezone("Asia/Tokyo")
TZ_HONGKONG = pytz.timezone("Asia/Hong_Kong")

now_berlin = datetime.now(TZ_BERLIN)
now_ny = datetime.now(TZ_NEWYORK)
now_tokyo = datetime.now(TZ_TOKYO)
now_hk = datetime.now(TZ_HONGKONG)

# === Handelszeiten prüfen ===
def is_market_open(market: str) -> bool:
    """Prüft, ob der jeweilige Markt gerade geöffnet ist."""
    weekday = now_berlin.weekday()
    if weekday >= 5:  # Wochenende
        return False

    if market == "XETRA":
        # Xetra (Deutschland): 09:00–17:30 Uhr (MEZ)
        return 9 <= now_berlin.hour < 17 or (now_berlin.hour == 17 and now_berlin.minute <= 30)

    elif market == "NYSE":
        # NYSE/Nasdaq (USA): 09:30–16:00 Uhr (New York Zeit)
        return (now_ny.hour > 9 or (now_ny.hour == 9 and now_ny.minute >= 30)) and now_ny.hour < 16

    elif market == "TOKYO":
        # Tokyo: 09:00–15:00 Uhr (Japan Zeit)
        return 9 <= now_tokyo.hour < 15

    elif market == "HONGKONG":
        # Hong Kong: 09:30–16:00 Uhr (Hongkong Zeit)
        return (now_hk.hour > 9 or (now_hk.hour == 9 and now_hk.minute >= 30)) and now_hk.hour < 16

    return False

# === Börse anhand Tickers erkennen ===
def detect_market(ticker_symbol: str) -> str:
    """Erkennt, zu welcher Börse der Ticker gehört."""
    ticker_symbol = ticker_symbol.upper()
    if ticker_symbol.endswith(".DE") or ticker_symbol.endswith(".F"):
        return "XETRA"
    elif ticker_symbol.endswith(".T"):
        return "TOKYO"
    elif ticker_symbol.endswith(".HK"):
        return "HONGKONG"
    else:
        return "NYSE"  # Default: US

# === Ticker einlesen ===
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f.readlines() if line.strip()]

output_data = []

print(f"🇩🇪 Berlin: {now_berlin.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🇺🇸 New York: {now_ny.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🇯🇵 Tokyo: {now_tokyo.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🇭🇰 Hong Kong: {now_hk.strftime('%Y-%m-%d %H:%M:%S')}\n")

for ticker_symbol in tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        market = detect_market(ticker_symbol)
        market_open = is_market_open(market)

        # === Live oder Tagesdaten ===
        if market_open:
            if market == "XETRA":
                interval = "15m"
            elif market in ["NYSE", "HONGKONG"]:
                interval = "5m"
            elif market == "TOKYO":
                interval = "10m"
            else:
                interval = "30m"

            data = ticker.history(period="1d", interval=interval)
        else:
            data = ticker.history(period="2d")

        if not data.empty:
            price = float(data["Close"].iloc[-1])
        else:
            price = None

        previous_close = ticker.info.get("previousClose", None)

        output_data.append({
            "ticker": ticker_symbol,
            "market": market,
            "price": price,
            "previous_close": previous_close
        })

        print(f"✅ {ticker_symbol} ({market}): {price} (Prev: {previous_close})")

        time.sleep(0.4)  # gegen Rate-Limits

    except Exception as e:
        print(f"⚠️ Fehler bei {ticker_symbol}: {e}")
        output_data.append({
            "ticker": ticker_symbol,
            "market": None,
            "price": None,
            "previous_close": None
        })

# === JSON schreiben ===
with open("monitor_output.json", "w") as f:
    json.dump(output_data, f, indent=4)

print("\n📈 monitor_output.json erfolgreich aktualisiert!")
