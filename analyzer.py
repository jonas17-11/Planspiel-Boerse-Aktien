import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64

# --- Assets ---
ASSET_NAMES = {
    # --- Währungen (Forex) ---
    "EURUSD=X": "Euro / US-Dollar",
    "USDJPY=X": "US-Dollar / Japanischer Yen",
    "GBPUSD=X": "Britisches Pfund / US-Dollar",
    "AUDUSD=X": "Australischer Dollar / US-Dollar",
    "USDCAD=X": "US-Dollar / Kanadischer Dollar",
    "USDCHF=X": "US-Dollar / Schweizer Franken",
    "NZDUSD=X": "Neuseeland-Dollar / US-Dollar",
    "EURGBP=X": "Euro / Britisches Pfund",
    "EURJPY=X": "Euro / Japanischer Yen",
    "EURCHF=X": "Euro / Schweizer Franken",
    "GBPJPY=X": "Britisches Pfund / Japanischer Yen",
    "AUDJPY=X": "Australischer Dollar / Japanischer Yen",
    "CHFJPY=X": "Schweizer Franken / Japanischer Yen",
    "EURNZD=X": "Euro / Neuseeland-Dollar",
    "USDNOK=X": "US-Dollar / Norwegische Krone",
    "USDDKK=X": "US-Dollar / Dänische Krone",
    "USDSEK=X": "US-Dollar / Schwedische Krone",
    "USDTRY=X": "US-Dollar / Türkische Lira",
    "USDMXN=X": "US-Dollar / Mexikanischer Peso",
    "USDCNH=X": "US-Dollar / Chinesischer Yuan",
    "GBPAUD=X": "Britisches Pfund / Australischer Dollar",
    "EURAUD=X": "Euro / Australischer Dollar",
    "EURCAD=X": "Euro / Kanadischer Dollar",

    # --- Edelmetalle & Rohstoffe ---
    "XAUUSD": "Gold",
    "XAGUSD": "Silber",
    "XPTUSD": "Platin",
    "XPDUSD": "Palladium",
    "WTI": "Rohöl (West Texas)",
    "BRENT": "Brent-Öl",
    "NG=F": "Erdgas",
    "HG=F": "Kupfer",
    "SI=F": "Silber (Futures)",
    "GC=F": "Gold (Futures)",
    "CL=F": "Crude Oil (Futures)",
    "PL=F": "Platin (Futures)",
    "PA=F": "Palladium (Futures)",
    "ZC=F": "Mais (Futures)",
    "ZS=F": "Sojabohnen (Futures)",
    "ZR=F": "Weizen (Futures)",
    "KC=F": "Kaffee",
    "SB=F": "Zucker",
    "CT=F": "Baumwolle",

    # --- Indizes ---
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "Nasdaq 100",
    "^GDAXI": "DAX 40",
    "^FCHI": "CAC 40",
    "^FTSE": "FTSE 100",
    "^N225": "Nikkei 225",
    "^HSI": "Hang Seng (Hong Kong)",
    "000001.SS": "Shanghai Composite",
    "^BVSP": "Bovespa",
    "^GSPTSE": "TSX Kanada",
    "^SSMI": "SMI Schweiz",
    "^AS51": "ASX 200 Australien",
    "^MXX": "IPC Mexiko",
    "^STOXX50E": "Euro Stoxx 50",
    "^IBEX": "IBEX 35 Spanien",
    "^NSEI": "Nifty 50 Indien",

    # --- Kryptowährungen ---
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "BNB-USD": "Binance Coin",
    "SOL-USD": "Solana",
    "XRP-USD": "Ripple",
    "ADA-USD": "Cardano",
    "DOGE-USD": "Dogecoin",
    "DOT-USD": "Polkadot",
    "AVAX-USD": "Avalanche",
    "LTC-USD": "Litecoin",
    "TRX-USD": "Tron",
    "LINK-USD": "Chainlink",
    "ATOM-USD": "Cosmos",
    "MATIC-USD": "Polygon",
    "UNI-USD": "Uniswap",
    "EOS-USD": "EOS",
    "FTT-USD": "FTX Token",
    "ALGO-USD": "Algorand",
    "XTZ-USD": "Tezos",
    "NEO-USD": "NEO",
    "AAVE-USD": "Aave",
    "COMP-USD": "Compound",
    "MKR-USD": "Maker",
    "SUSHI-USD": "SushiSwap",
    "FIL-USD": "Filecoin",
    "ICP-USD": "Internet Computer",
    "LUNA-USD": "Terra",
    "CEL-USD": "Celsius",
    "RVN-USD": "Ravencoin",
    "KSM-USD": "Kusama",
    "ENJ-USD": "Enjin Coin",
    "CHZ-USD": "Chiliz"
}

# --- Assets aus prognose.txt laden ---
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

# --- Daten abrufen ---
def fetch_data(ticker, period="1mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        df = df.dropna()
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

# --- Candlestick Mustererkennung (kurzfristig) ---
def detect_candlestick(df):
    if df is None or len(df) < 2:
        return "Keine Daten", 0
    open_ = df['Open'].iloc[-2:]
    close = df['Close'].iloc[-2:]
    high = df['High'].iloc[-2:]
    low = df['Low'].iloc[-2:]
    
    # Einfaches Beispiel: Bullish/Bearish Engulfing
    if close.iloc[-2] < open_.iloc[-2] and close.iloc[-1] > open_.iloc[-1] and close.iloc[-1] > open_.iloc[-2]:
        return "Bullish Engulfing 📈", 0.7
    elif close.iloc[-2] > open_.iloc[-2] and close.iloc[-1] < open_.iloc[-1] and close.iloc[-1] < open_.iloc[-2]:
        return "Bearish Engulfing 📉", 0.7
    elif abs(close.iloc[-1] - open_.iloc[-1]) / (high.iloc[-1] - low.iloc[-1] + 1e-6) < 0.1:
        return "Doji ➖", 0.5
    else:
        # Trend kurzfristig
        change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
        if change > 0.01:
            return "Kurzfristig steigend 📈", round(change*100,2)
        elif change < -0.01:
            return "Kurzfristig fallend 📉", round(-change*100,2)
        else:
            return "Seitwärts ➖", round(change*100,2)

# --- Prognose einfacher linearer Trend ---
def forecast_next(df, days=3):
    if df is None or len(df) < 2:
        return None
    close = df['Close'].values
    x = np.arange(len(close))
    coef = np.polyfit(x, close, 1)
    trend = np.poly1d(coef)
    future_x = np.arange(len(close), len(close)+days)
    pred = trend(future_x)
    return pred

# --- Liniendiagramm erstellen ---
def create_chart(df, forecast, ticker):
    plt.figure(figsize=(8,4))
    plt.plot(df.index, df['Close'], label="Aktueller Kurs", color="blue")
    if forecast is not None:
        future_index = [df.index[-1] + timedelta(days=i+1) for i in range(len(forecast))]
        plt.plot(future_index, forecast, label="Prognose", color="red")
    plt.title(f"{ASSET_NAMES.get(ticker,ticker)} Kursverlauf")
    plt.ylabel("Preis")
    plt.legend()
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"

# --- Analyse und Zusammenfassung ---
def analyze_asset(ticker):
    df = fetch_data(ticker)
    pattern, confidence = detect_candlestick(df)
    forecast = forecast_next(df)
    last_price = df['Close'].iloc[-1] if df is not None and not df.empty else None
    chart = create_chart(df, forecast, ticker)
    return {
        "ticker": ticker,
        "name": ASSET_NAMES.get(ticker, ticker),
        "pattern": pattern,
        "confidence": confidence,
        "last_price": last_price,
        "chart": chart
    }

def get_analysis():
    results = []
    for ticker in assets:
        res = analyze_asset(ticker)
        results.append(res)
    # Sortiere aufsteigend/absteigend nach letztem Kurs-Change
    results_sorted_up = sorted(results, key=lambda x: x["confidence"], reverse=True)[:10]
    results_sorted_down = sorted(results, key=lambda x: x["confidence"])[:10]
    return results_sorted_up, results_sorted_down
