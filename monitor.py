#!/usr/bin/env python3
# monitor.py
import yfinance as yf
import pandas as pd
import json
import time
from datetime import datetime

TICKERS_FILE = "tickers.txt"
OUTPUT_FILE = "monitor_output.json"
BATCH_SIZE = 50          # Anzahl Ticker pro Batch (reduziert Anzahl Requests)
INTERVAL = "5m"
PERIOD = "1d"

def read_tickers():
    with open(TICKERS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def process_batch(batch):
    results = []
    try:
        # Batch-Download (effizienter als Einzel-Requests)
        df = yf.download(tickers=" ".join(batch), period=PERIOD, interval=INTERVAL,
                         group_by="ticker", threads=True, progress=False)
    except Exception as e:
        print("Batch-download fehlgeschlagen:", e)
        return results

    for ticker in batch:
        try:
            # Unterschiedliche Rückgabe-Formate abfangen
            ticker_df = None
            if isinstance(df.columns, pd.MultiIndex):
                # Gruppiert nach ticker: df.xs works
                try:
                    ticker_df = df.xs(ticker, axis=1, level=1)
                except Exception:
                    # alternativ: viele Versionen von yfinance unterschieden
                    if ticker in df.columns:
                        ticker_df = df[ticker]
            else:
                if ticker in df.columns:
                    ticker_df = df[ticker]

            # Manche Rückgaben liefern nur eine Serie / DataFrame mit numeric columns
            if ticker_df is None:
                continue

            # Wähle 'Close' oder 'Adj Close' oder erste numerische Spalte
            if isinstance(ticker_df, pd.DataFrame):
                if "Close" in ticker_df.columns:
                    series = ticker_df["Close"].dropna()
                elif "Adj Close" in ticker_df.columns:
                    series = ticker_df["Adj Close"].dropna()
                else:
                    # fallback: erste numerische Spalte
                    numeric_cols = [c for c in ticker_df.columns if pd.api.types.is_numeric_dtype(ticker_df[c])]
                    if numeric_cols:
                        series = ticker_df[numeric_cols[0]].dropna()
                    else:
                        continue
            else:
                # Serie
                series = ticker_df.dropna()

            if len(series) < 2:
                continue
            last = float(series.iloc[-1])
            prev = float(series.iloc[-2])
            if prev == 0:
                continue
            pct = ((last - prev) / prev) * 100.0
            results.append({
                "ticker": ticker,
                "price": round(last, 2),
                "percent_change": round(pct, 2)
            })
        except Exception as e:
            print(f"Fehler bei {ticker}: {e}")
            continue

    return results

def main():
    tickers = read_tickers()
    all_results = []

    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        print(f"Verarbeite Batch {i}..{i+len(batch)} ({len(batch)} Ticker)")
        res = process_batch(batch)
        all_results.extend(res)
        time.sleep(1)  # kurze Pause zwischen Batches

    if not all_results:
        print("Keine Daten abgerufen.")
        return

    # Sortiere nach Prozentänderung (desc)
    df = pd.DataFrame(all_results)
    df = df.sort_values("percent_change", ascending=False)

    out = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": df.to_dict(orient="records")
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"{OUTPUT_FILE} geschrieben mit {len(out['data'])} Einträgen.")

if __name__ == "__main__":
    main()
