import yfinance as yf
import pandas as pd
import mplfinance as mpf
import os
from datetime import timedelta

# --- Mapping Ticker -> Ausgeschriebener Name ---
ASSET_NAMES = {
    "EURUSD": "Euro / US-Dollar", "USDJPY": "US-Dollar / Japanischer Yen",
    "GBPUSD": "Britisches Pfund / US-Dollar", "AUDUSD": "Australischer Dollar / US-Dollar",
    "USDCAD": "US-Dollar / Kanadischer Dollar", "USDCHF": "US-Dollar / Schweizer Franken",
    "NZDUSD": "Neuseeland-Dollar / US-Dollar", "EURGBP": "Euro / Britisches Pfund",
    "EURJPY": "Euro / Japanischer Yen", "EURCHF": "Euro / Schweizer Franken",
    "GBPJPY": "Britisches Pfund / Japanischer Yen", "AUDJPY": "Australischer Dollar / Japanischer Yen",
    "CHFJPY": "Schweizer Franken / Japanischer Yen", "EURNZD": "Euro / Neuseeland-Dollar",
    "USDNOK": "US-Dollar / Norwegische Krone", "USDDKK": "US-Dollar / Dänische Krone",
    "USDSEK": "US-Dollar / Schwedische Krone", "USDTRY": "US-Dollar / Türkische Lira",
    "USDMXN": "US-Dollar / Mexikanischer Peso", "USDCNH": "US-Dollar / Chinesischer Yuan",
    "GBPAUD": "Britisches Pfund / Australischer Dollar", "EURAUD": "Euro / Australischer Dollar",
    "EURCAD": "Euro / Kanadischer Dollar",
    "XAUUSD": "Gold", "XAGUSD": "Silber", "XPTUSD": "Platin", "XPDUSD": "Palladium",
    "WTI": "Rohöl (West Texas)", "BRENT": "Brent-Öl"
    # Du kannst weitere Assets hinzufügen
}

# --- Assets aus prognose.txt ---
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

def fetch_data(ticker, period="7d", interval="1h"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

def analyze_pattern(df):
    if df is None or df.empty:
        return "Keine Daten", 0
    start = df["Close"].iloc[0]
    end = df["Close"].iloc[-1]
    change = (end - start) / start
    if change > 0.002:
        return "Aufwärts-Trend 📈", round(change*100,2)
    elif change < -0.002:
        return "Abwärts-Trend 📉", round(change*100,2)
    else:
        return "Seitwärts-Trend ➖", round(change*100,2)

def create_candlestick(df, ticker, forecast_steps=5):
    if df is None or df.empty:
        return None
    # Prognose (einfach linear)
    last_price = float(df["Close"].iloc[-1])
    forecast = [last_price * (1 + 0.001*i) for i in range(1, forecast_steps+1)]
    future_index = [df.index[-1] + timedelta(hours=i) for i in range(1, forecast_steps+1)]
    forecast_df = pd.DataFrame({"Open": forecast, "High": forecast, "Low": forecast, "Close": forecast}, index=future_index)

    plot_df = pd.concat([df, forecast_df])
    mc = mpf.make_marketcolors(up='#1f77b4', down='#ff3333', edge='i', wick='i', volume='in')
    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=False)
    chart_path = f"charts/{ticker}.png"
    os.makedirs("charts", exist_ok=True)
    mpf.plot(plot_df, type='candle', style=s, title=ASSET_NAMES.get(ticker,ticker),
             ylabel='Preis', figratio=(8,4), savefig=chart_path, tight_layout=True)
    return chart_path

def get_analysis():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        pattern, confidence = analyze_pattern(df)
        chart = create_candlestick(df, ticker)
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "confidence": confidence,
            "chart": chart
        })
    top = sorted(results, key=lambda x:x["confidence"], reverse=True)[:10]
    flop = sorted(results, key=lambda x:x["confidence"])[:10]
    return top, flop
