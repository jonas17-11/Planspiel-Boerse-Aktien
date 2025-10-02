#!/usr/bin/env python3
import os
import json
import time
import yfinance as yf
import pandas as pd
import requests

# --- Konfiguration ---
TICKERS = [t.strip().upper() for t in os.getenv("TICKERS", "AAPL,MSFT,GOOG").split(",")]
GAME_API = os.getenv("GAME_API_URL", "").strip() or None
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.5"))
MOMENTUM_PERIOD = int(os.getenv("MOMENTUM_PERIOD", "5"))  # Anzahl Kerzen für Momentum
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))           # RSI Zeitraum
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

HTTP_TIMEOUT = 10

# --- Funktionen ---
def fetch_market_data(tickers):
    """Lädt Kursdaten der letzten RSI_PERIOD+MOMENTUM_PERIOD Kerzen."""
    try:
        data = yf.download(tickers=tickers, period="7d", interval="1h", progress=False)
        return data
    except Exception as e:
        print("Fehler beim Abrufen der Marktpreise:", e)
        return None

def fetch_game_price(symbol: str):
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

def compute_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_telegram(message: str):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        return
    try:
        api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(api, data=payload, timeout=HTTP_TIMEOUT)
    except Exception as e:
        print("Telegram-Fehler:", e)

# --- Main ---
def main():
    ts = int(time.time())
    results = []

    market_data = fetch_market_data(TICKERS)
    if market_data is None:
        print("Keine Kursdaten verfügbar.")
        return

    for sym in TICKERS:
        entry = {"symbol": sym, "market": None, "game": None, "delta": None,
                 "momentum": None, "rsi": None, "recommend": False, "error": None}

        try:
            if len(TICKERS) == 1:
                series = market_data['Close']
            else:
                series = market_data['Close'][sym]
            current_price = series.iloc[-1]
            entry["market"] = float(current_price)

            # --- Momentum ---
            if len(series) >= MOMENTUM_PERIOD + 1:
                momentum = (series.iloc[-1] - series.iloc[-MOMENTUM_PERIOD-1]) / series.iloc[-MOMENTUM_PERIOD-1]
                entry["momentum"] = round(momentum, 4)
            else:
                entry["momentum"] = 0

            # --- RSI ---
            if len(series) >= RSI_PERIOD + 1:
                rsi_series = compute_rsi(series, period=RSI_PERIOD)
                entry["rsi"] = round(rsi_series.iloc[-1], 2)
            else:
                entry["rsi"] = None

            # --- Spielpreis Delta ---
            game_price = fetch_game_price(sym)
            entry["game"] = game_price
            if game_price is not None:
                entry["delta"] = current_price - game_price

            # --- Empfehlung: Delta oder Momentum & RSI ---
            if (entry["delta"] is not None and abs(entry["delta"]) >= ALERT_THRESHOLD) or \
               (entry["momentum"] > 0 and (entry["rsi"] is None or entry["rsi"] < 70)):
                entry["recommend"] = True
                msg = f"RECOMMEND {sym}: Markt={current_price:.2f} Δ={entry['delta']} " \
                      f"Momentum={entry['momentum']} RSI={entry['rsi']}"
                print(msg)
                if TELEGRAM_ENABLED:
                    send_telegram(msg)

        except Exception as e:
            entry["error"] = str(e)

        results.append(entry)

    # JSON Output
    output_file = "monitor_output.json"
    with open(output_file, "w") as f:
        json.dump({"timestamp": ts, "results": results}, f, indent=2)
    print(f"Fertig. Ergebnisse geschrieben: {output_file}")

if __name__ == "__main__":
    main()
