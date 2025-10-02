#!/usr/bin/env python3
# monitor.py
import os
import json
import time
import yfinance as yf
import requests

# --- Konfiguration ---
TICKERS = [t.strip().upper() for t in os.getenv("TICKERS", "AAPL,MSFT,GOOG").split(",")]
GAME_API = os.getenv("GAME_API_URL", "").strip() or None
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.5"))
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

HTTP_TIMEOUT = 10

# --- Funktionen ---
def fetch_market_prices(tickers):
    """Holt alle Kurse in einem Request via yfinance."""
    try:
        data = yf.download(tickers=tickers, period="1d", interval="1m", progress=False)
        if len(tickers) == 1:
            return {tickers[0]: float(data['Close'].iloc[-1])}
        else:
            return {t: float(data['Close'][t].iloc[-1]) for t in tickers}
    except Exception as e:
        print("Fehler beim Abrufen der Marktpreise:", e)
        return {}

def fetch_game_price(symbol: str):
    """Optional: Preis aus Spiel-API"""
    if not GAME_API:
        return None
    try:
        url = GAME_API.replace("{symbol}", symbol)
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        if isinstance(j, (int, float, str)):
            return float(j)
        if isinstance(j, dict):
            if "price" in j:
                return float(j["price"])
            for v in j.values():
                if isinstance(v, (int, float)):
                    return float(v)
    except Exception as e:
        print(f"Fehler Game API {symbol}: {e}")
    return None

def send_telegram(message: str):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram nicht konfiguriert.")
        return
    try:
        api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(api, data=payload, timeout=HTTP_TIMEOUT)
    except Exception as e:
        print("Fehler beim Telegram-Senden:", e)

# --- Main ---
def main():
    ts = int(time.time())
    results = []

    market_prices = fetch_market_prices(TICKERS)
    for sym in TICKERS:
        entry = {"symbol": sym, "market": None, "game": None, "delta": None, "error": None}

        market = market_prices.get(sym)
        if market is None:
            entry["error"] = "Marktpreis nicht verfügbar"
            results.append(entry)
            continue
        entry["market"] = market

        # Spielpreis
        game = fetch_game_price(sym)
        entry["game"] = game
        if game is not None:
            entry["delta"] = market - game

        results.append(entry)

        # Alerting
        if entry["delta"] is not None and abs(entry["delta"]) >= ALERT_THRESHOLD:
            msg = f"ALERT {sym}: Markt={entry['market']:.2f} Spiel={entry['game']:.2f} Δ={entry['delta']:.2f}"
            print(msg)
            if TELEGRAM_ENABLED:
                send_telegram(msg)

    # JSON Output für Artifact
    output_file = "monitor_output.json"
    with open(output_file, "w") as f:
        json.dump({"timestamp": ts, "results": results}, f, indent=2)
    print(f"Fertig. Ergebnisse geschrieben: {output_file}")

if __name__ == "__main__":
    main()
