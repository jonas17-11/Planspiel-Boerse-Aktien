import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- Mapping Ticker -> Vollständiger Name ---
ASSET_NAMES = {
    # Währungen (Forex)
    "EURUSD=X": "Euro / US-Dollar", "USDJPY=X": "US-Dollar / Japanischer Yen", "GBPUSD=X": "Britisches Pfund / US-Dollar", "AUDUSD=X": "Australischer Dollar / US-Dollar", "USDCAD=X": "US-Dollar / Kanadischer Dollar", "USDCHF=X": "US-Dollar / Schweizer Franken", "NZDUSD=X": "Neuseeland-Dollar / US-Dollar", "EURGBP=X": "Euro / Britisches Pfund", "EURJPY=X": "Euro / Japanischer Yen", "EURCHF=X": "Euro / Schweizer Franken", "GBPJPY=X": "Britisches Pfund / Japanischer Yen", "AUDJPY=X": "Australischer Dollar / Japanischer Yen", "CHFJPY=X": "Schweizer Franken / Japanischer Yen", "EURNZD=X": "Euro / Neuseeland-Dollar", "USDNOK=X": "US-Dollar / Norwegische Krone", "USDDKK=X": "US-Dollar / Dänische Krone", "USDSEK=X": "US-Dollar / Schwedische Krone", "USDTRY=X": "US-Dollar / Türkische Lira", "USDMXN=X": "US-Dollar / Mexikanischer Peso", "USDCNH=X": "US-Dollar / Chinesischer Yuan", "GBPAUD=X": "Britisches Pfund / Australischer Dollar", "EURAUD=X": "Euro / Australischer Dollar", "EURCAD=X": "Euro / Kanadischer Dollar", # Edelmetalle & Rohstoffe 
    "XAUUSD": "Gold", "XAGUSD": "Silber", "XPTUSD": "Platin", "XPDUSD": "Palladium", "WTI": "Rohöl (West Texas)", "BRENT": "Brent-Öl", "NG=F": "Erdgas", "HG=F": "Kupfer", "SI=F": "Silber (Futures)", "GC=F": "Gold (Futures)", "CL=F": "Crude Oil (Futures)", "PL=F": "Platin (Futures)", "PA=F": "Palladium (Futures)", "ZC=F": "Mais (Futures)", "ZS=F": "Sojabohnen (Futures)", "ZR=F": "Weizen (Futures)", "KC=F": "Kaffee", "SB=F": "Zucker", "CT=F": "Baumwolle", 
    # Indizes 
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "Nasdaq 100", "^GDAXI": "DAX 40", "^FCHI": "CAC 40", "^FTSE": "FTSE 100", "^N225": "Nikkei 225", "^HSI": "Hang Seng (Hong Kong)", "000001.SS": "Shanghai Composite", "^BVSP": "Bovespa", "^GSPTSE": "TSX Kanada", "^SSMI": "SMI Schweiz", "^AS51": "ASX 200 Australien", "^MXX": "IPC Mexiko", "^STOXX50E": "Euro Stoxx 50", "^IBEX": "IBEX 35 Spanien", "^NSEI": "Nifty 50 Indien", 
    # Kryptowährungen 
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin", "SOL-USD": "Solana", "XRP-USD": "Ripple", "ADA-USD": "Cardano", "DOGE-USD": "Dogecoin", "DOT-USD": "Polkadot", "AVAX-USD": "Avalanche", "LTC-USD": "Litecoin", "TRX-USD": "Tron", "LINK-USD": "Chainlink", "ATOM-USD": "Cosmos", "MATIC-USD": "Polygon", "UNI-USD": "Uniswap", "EOS-USD": "EOS", "FTT-USD": "FTX Token", "ALGO-USD": "Algorand", "XTZ-USD": "Tezos", "NEO-USD": "NEO", "AAVE-USD": "Aave", "COMP-USD": "Compound", "MKR-USD": "Maker", "SUSHI-USD": "SushiSwap", "FIL-USD": "Filecoin", "ICP-USD": "Internet Computer", "LUNA-USD": "Terra", "CEL-USD": "Celsius", "RVN-USD": "Ravencoin", "KSM-USD": "Kusama", "ENJ-USD": "Enjin Coin", "CHZ-USD": "Chiliz"
}

# --- Assets aus prognose.txt laden ---
with open("prognose.txt", "r") as f:
    ASSETS = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

# --- Candlestick-Erkennung (erweitert) ---
def detect_candlestick(df: pd.DataFrame):
    if len(df) < 2:
        return "Neutral", "up", 50.0

    df = df.copy()
    df["Body"] = df["Close"] - df["Open"]
    df["Range"] = df["High"] - df["Low"]

    last, prev = df.iloc[-1], df.iloc[-2]
    last_body = float(last["Body"])
    prev_body = float(prev["Body"])

    last_open, last_close = float(last["Open"]), float(last["Close"])
    last_high, last_low = float(last["High"]), float(last["Low"])

    pattern = "Neutral"
    trend = "up"

    # Bullish Engulfing
    if prev_body < 0 and last_body > 0 and last_close > prev["Open"] and abs(last_body) > abs(prev_body):
        pattern, trend = "Bullish Engulfing", "up"
    # Bearish Engulfing
    elif prev_body > 0 and last_body < 0 and last_close < prev["Open"] and abs(last_body) > abs(prev_body):
        pattern, trend = "Bearish Engulfing", "down"
    # Doji
    elif abs(last_body) < 0.1 * (last_high - last_low):
        pattern, trend = "Doji", "neutral"
    # Hammer
    elif last_body > 0 and (last_low < last_open - 2 * abs(last_body)):
        pattern, trend = "Hammer", "up"
    # Shooting Star
    elif last_body < 0 and (last_high > last_open + 2 * abs(last_body)):
        pattern, trend = "Shooting Star", "down"
    else:
        trend = "up" if last_close > last_open else "down"

    confidence = min(abs(last_body) / max(last_open, 0.0001) * 80, 100)
    return pattern, trend, round(confidence, 2)


# --- Prognose (lineares Modell) ---
def predict(df: pd.DataFrame, days_ahead: int = 5):
    df = df.tail(30).copy()  # letzte 30 Tage für Kurzfristprognose
    df["t"] = np.arange(len(df))
    coef = np.polyfit(df["t"], df["Close"], 1)
    poly = np.poly1d(coef)

    future_t = np.arange(len(df), len(df) + days_ahead)
    future_dates = [df.index[-1] + timedelta(days=i + 1) for i in range(days_ahead)]
    future_preds = poly(future_t)

    forecast_df = pd.DataFrame({"Predicted": future_preds}, index=future_dates)
    return forecast_df


# --- Daten holen ---
def fetch_data(ticker, period="3mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        return df if not df.empty else None
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None


# --- Hauptanalyse ---
def analyze_and_predict_all():
    results = []
    for ticker in ASSETS:
        df = fetch_data(ticker)
        if df is None:
            continue
        pattern, trend, confidence = detect_candlestick(df)
        forecast_df = predict(df)
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "trend": trend,
            "confidence": confidence,
            "df": df,
            "forecast_df": forecast_df
        })

    # sortieren
    top_up = sorted([r for r in results if r["trend"] == "up"], key=lambda x: x["confidence"], reverse=True)[:5]
    top_down = sorted([r for r in results if r["trend"] == "down"], key=lambda x: x["confidence"], reverse=True)[:5]
    return top_up, top_down
