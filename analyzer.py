import yfinance as yf
import pandas as pd
import numpy as np

# --- Mapping Ticker -> Name ---
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

# --- Assets Liste ---
ASSETS = list(ASSET_NAMES.keys())

# --- Daten abrufen ---
def fetch_data(ticker, period="1mo", interval="1h"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

# --- Candlestick-Muster erkennen ---
def detect_candlestick(df):
    """
    Sehr einfache Mustererkennung:
    - Bullish Engulfing: Aufwärts-Trend Signal
    - Bearish Engulfing: Abwärts-Trend Signal
    """
    df['Body'] = df['Close'] - df['Open']
    df['PrevBody'] = df['Body'].shift(1)

    pattern = "Neutral"
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Bullish Engulfing
    if prev['Body'] < 0 and last['Body'] > 0 and abs(last['Body']) > abs(prev['Body']):
        pattern = "Bullish Engulfing"
        trend = 'up'
    # Bearish Engulfing
    elif prev['Body'] > 0 and last['Body'] < 0 and abs(last['Body']) > abs(prev['Body']):
        pattern = "Bearish Engulfing"
        trend = 'down'
    else:
        trend = 'up' if last['Close'] > last['Open'] else 'down'

    confidence = min(abs(last['Body']) / last['Open'] * 100 * 2, 100)  # einfache Prozentangabe
    return pattern, trend, round(confidence,2)

# --- Prognose erstellen (einfacher linearer Trend) ---
def forecast(df, hours=24):
    last_close = df['Close'].iloc[-1]
    changes = df['Close'].pct_change().fillna(0)
    avg_change = changes[-20:].mean()  # Durchschnitt der letzten 20 Perioden
    predicted_values = [last_close * (1 + avg_change * (i+1)) for i in range(hours)]
    future_index = pd.date_range(df.index[-1], periods=hours+1, freq=df.index.freq)[1:]
    forecast_df = pd.DataFrame({"Predicted": predicted_values}, index=future_index)
    return forecast_df

# --- Hauptfunktion ---
def analyze_and_predict_all():
    results = []
    for ticker in ASSETS:
        df = fetch_data(ticker)
        if df is None or df.empty:
            continue
        pattern, trend, confidence = detect_candlestick(df)
        forecast_df = forecast(df)
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "trend": trend,
            "confidence": confidence,
            "pattern": pattern,
            "df": df,
            "forecast_df": forecast_df
        })
    return results
