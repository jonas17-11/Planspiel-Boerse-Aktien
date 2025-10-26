import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Alle Assets ---
ASSETS = [
    # Währungen (Forex)
    "EURUSD=X","USDJPY=X","GBPUSD=X","AUDUSD=X","USDCAD=X","USDCHF=X",
    "NZDUSD=X","EURGBP=X","EURJPY=X","EURCHF=X","GBPJPY=X","AUDJPY=X",
    "CHFJPY=X","EURNZD=X","USDNOK=X","USDDKK=X","USDSEK=X","USDTRY=X",
    "USDMXN=X","USDCNH=X","GBPAUD=X","EURAUD=X","EURCAD=X",
    # Edelmetalle & Rohstoffe
    "XAUUSD","XAGUSD","XPTUSD","XPDUSD","WTI","BRENT","NG=F","HG=F",
    "SI=F","GC=F","CL=F","PL=F","PA=F","ZC=F","ZS=F","ZR=F","KC=F",
    "SB=F","CT=F",
    # Indizes
    "^GSPC","^DJI","^IXIC","^GDAXI","^FCHI","^FTSE","^N225","^HSI",
    "000001.SS","^BVSP","^GSPTSE","^SSMI","^AS51","^MXX","^STOXX50E",
    "^IBEX","^NSEI",
    # Kryptowährungen
    "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD","DOGE-USD",
    "DOT-USD","AVAX-USD","LTC-USD","TRX-USD","LINK-USD","ATOM-USD",
    "MATIC-USD","UNI-USD","EOS-USD","FTT-USD","ALGO-USD","XTZ-USD",
    "NEO-USD","AAVE-USD","COMP-USD","MKR-USD","SUSHI-USD","FIL-USD",
    "ICP-USD","LUNA-USD","CEL-USD","RVN-USD","KSM-USD","ENJ-USD","CHZ-USD"
]

# --- Asset Names ---
ASSET_NAMES = {asset: asset for asset in ASSETS}

# --- Daten laden ---
def fetch_data(ticker, period="1mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

# --- Candlestick-Mustererkennung ---
def detect_candlestick(df):
    if len(df) < 2:
        return "Neutral", "up", 50.0
    df = df.copy()
    df['Body'] = df['Close'] - df['Open']
    last = df.iloc[-1]
    prev = df.iloc[-2]
    last_body = float(last['Body'])
    prev_body = float(prev['Body'])

    pattern = "Neutral"
    trend = "up"

    # Bullish Engulfing
    if prev_body < 0 and last_body > 0 and abs(last_body) > abs(prev_body):
        pattern = "Bullish Engulfing"
        trend = 'up'
    # Bearish Engulfing
    elif prev_body > 0 and last_body < 0 and abs(last_body) > abs(prev_body):
        pattern = "Bearish Engulfing"
        trend = 'down'
    else:
        trend = 'up' if last['Close'] > last['Open'] else 'down'

    confidence = min(abs(last_body) / last['Open'] * 100 * 2, 100)
    return pattern, trend, round(confidence,2)

# --- Prognosefunktion (einfach linear basierend auf letzten 5 Tagen) ---
def forecast_next(df, days=5):
    df = df.copy()
    if len(df) < 5:
        return pd.DataFrame()
    df['Close_shift'] = df['Close'].shift(1)
    df['Change'] = df['Close'] - df['Close_shift']
    mean_change = df['Change'].iloc[-5:].mean()
    last_close = df['Close'].iloc[-1]
    forecast_values = [last_close + mean_change*(i+1) for i in range(days)]
    future_dates = pd.date_range(start=df.index[-1]+pd.Timedelta(days=1), periods=days)
    forecast_df = pd.DataFrame({"Date": future_dates, "Predicted": forecast_values})
    return forecast_df

# --- Analyse aller Assets ---
def analyze_and_predict_all():
    results = []
    for ticker in ASSETS:
        df = fetch_data(ticker)
        if df is None:
            continue
        pattern, trend, confidence = detect_candlestick(df)
        forecast_df = forecast_next(df)
        current_price = df['Close'].iloc[-1]
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "trend": trend,
            "confidence": confidence,
            "current_price": current_price,
            "history": df,
            "forecast": forecast_df
        })
    return results

# --- Diagramm erstellen ---
def plot_asset(df, forecast_df, ticker):
    plt.figure(figsize=(10,5))
    plt.plot(df.index, df['Close'], label='Kurs', color='blue')
    if not forecast_df.empty:
        plt.plot(forecast_df['Date'], forecast_df['Predicted'], label='Prognose', color='red', linestyle='--')
    plt.title(f"{ticker}")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
    filename = f"{ticker.replace('^','')}.png"
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename
