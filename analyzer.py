# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np

# --- Mapping Ticker -> Ausgeschriebener Name ---
ASSET_NAMES = {
    # Währungen (Forex)
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
    # Edelmetalle & Rohstoffe
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
    # Indizes
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
    # Kryptowährungen
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

# --- Assets laden ---
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

def fetch_data(ticker, period="7d", interval="1h"):
    """Lade historische Kursdaten für das Asset."""
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

def detect_candlestick_pattern(df):
    """Einfache kurzfristige Candlestick-Erkennung."""
    if df is None or len(df) < 3:
        return "Keine Daten", 0, 0
    patterns = []

    o, h, l, c = df["Open"].iloc[-1], df["High"].iloc[-1], df["Low"].iloc[-1], df["Close"].iloc[-1]
    body = abs(c - o)
    lower_shadow = o - l if c >= o else c - l
    upper_shadow = h - c if c >= o else h - o

    if lower_shadow > 2 * body and upper_shadow < body:
        patterns.append("Hammer")
    if upper_shadow > 2 * body and lower_shadow < body:
        patterns.append("Shooting Star")

    if len(df) >= 2:
        prev_o, prev_c = df["Open"].iloc[-2], df["Close"].iloc[-2]
        if c > o and prev_c < prev_o and o < prev_c and c > prev_o:
            patterns.append("Bullish Engulfing")
        if c < o and prev_c > prev_o and o > prev_c and c < prev_o:
            patterns.append("Bearish Engulfing")

    pattern = ", ".join(patterns) if patterns else "Keine erkennbare Formation"
    change = (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]
    confidence = min(abs(change) * 100 * 2, 100)
    return pattern, confidence, change

def forecast_trend(df):
    """Lineare Prognose der nächsten 5 Stunden."""
    if df is None or len(df) < 2:
        return None
    last_idx = df.index[-1]
    future_dates = pd.date_range(start=last_idx + pd.Timedelta(hours=1), periods=5, freq="H")
    last_close = df["Close"].iloc[-1]
    trend_slope = df["Close"].pct_change().rolling(3).mean().iloc[-1]
    predicted = last_close * (1 + trend_slope) ** np.arange(1, 6)
    forecast_df = pd.DataFrame({"Predicted": predicted}, index=future_dates)
    return forecast_df

def analyze_and_predict_all():
    """Analyse für alle Assets."""
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        pattern, confidence, change = detect_candlestick_pattern(df)
        forecast_df = forecast_trend(df)
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "confidence": confidence,
            "change": change,
            "df": df,
            "forecast": forecast_df
        })
    return results
