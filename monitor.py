#!/usr/bin/env python3
# monitor.py
import os
import time
import json
import requests

# --- Konfiguration via Umgebungsvariablen (setze in GitHub Secrets) ---
# Kommagetrennte Ticker, z.B. "AAPL,MSFT,GOOG"
TICKERS = [t.strip().upper() for t in os.getenv("TICKERS", "AAPL,MSFT,GOOG").split(",")]

# Optional: URL zu eurer Spiel-API; {symbol} wird ersetzt. Beispiel:
# https://dein-spiel.example/api/price?symbol={symbol}
GAME_API = os.getenv("GAME_API_URL", "").strip() or None

# Alert-Schwelle (in Währungseinheit, z.B. USD). Wenn |market - game| >= ALERT_THRESHOLD -> Alert.
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.5"))

# Telegram (optional)
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Timeout für HTTP-Requests
HTTP_TIMEOUT = 10

# --- Funktionen ---
def fetch_market_price(symbol: str) -> float:
    """Holt aktuellen Kurs von Yahoo Finance (öffentlicher JSON-Endpoint)."""
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    resp = requests.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("quoteResponse", {}).get("result", [])
    if not result:
        raise ValueError(f"Keine Marktdaten für {symbol}")
    price = result[0].get("regularMarketPrice") or result[0].get("regularMarketPreviousClose")
    if price is None:
        raise ValueError(f"Kein Preisfeld für {symbol}")
    return float(price)

def fetch_game_price(symbol: str):
    """Holt optional Preis aus Spiel-API. Erwartet JSON mit {"price": number}."""
    if not GAME_API:
        return None
    url = GAME_API.replace("{symbol}", symbol)
    resp = requests.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    j = resp.json()
    # flexible: unterstütze direkte Zahl oder {"price": number}
    if isinstance(j, (int, float, str)):
        return float(j)
    if isinstance(j, dict):
        if "price" in j:
            return float(j["price"])
        # versuche erste numerische value
        for v in j.values():
            if isinstance(v, (int, float)):
                return float(v)
    raise ValueError("Spiel-API: kein Preis gefunden im JSON")

def send_telegram(message: str):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram nicht konfiguriert (Token/Chat fehlen).")
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        r = requests.post(api, data=payload, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print("Fehler beim Senden von Telegram:", e)

def main():
    results = []
    ts = int(time.time())
    for sym in TICKERS:
        entry = {"symbol": sym, "market": None, "game": None, "delta": None, "error": None}
        try:
            market = fetch_market_price(sym)
            entry["market"] = market
        except Exception as e:
            entry["error"] = f"Marktfehler: {e}"
            print(entry["error"])
            results.append(entry)
            continue

        if GAME_API:
            try:
                game = fetch_game_price(sym)
                entry["game"] = game
                entry["delta"] = market - game if game is not None else None
            except Exception as e:
                entry["error"] = f"Game API Fehler: {e}"
                print(entry["error"])

        results.append(entry)
        # Alerting
        if entry["delta"] is not None and abs(entry["delta"]) >= ALERT_THRESHOLD:
            msg = f"ALERT {sym}: Markt={entry['market']:.2f} Spiel={entry['game']:.2f} Δ={entry['delta']:.2f}"
            print(msg)
            if TELEGRAM_ENABLED:
                send_telegram(msg)

    # Schreibe lokal JSON (wird als Artifact in Action hochgeladen)
    out = {"timestamp": ts, "results": results}
    with open("monitor_output.json", "w") as f:
        json.dump(out, f, indent=2)
    print("Fertig. Ergebnisse geschrieben: monitor_output.json")

if __name__ == "__main__":
    main()
