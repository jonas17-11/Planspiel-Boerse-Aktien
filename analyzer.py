import yfinance as yf
import pandas as pd
import numpy as np

# --- Asset Names ---
ASSET_NAMES = {
    # Währungen (Forex)
    "EURUSD=X": "Euro / US-Dollar", "USDJPY=X": "US-Dollar / Japanischer Yen", "GBPUSD=X": "Britisches Pfund / US-Dollar",
    "AUDUSD=X": "Australischer Dollar / US-Dollar", "USDCAD=X": "US-Dollar / Kanadischer Dollar", "USDCHF=X": "US-Dollar / Schweizer Franken",
    "NZDUSD=X": "Neuseeland-Dollar / US-Dollar", "EURGBP=X": "Euro / Britisches Pfund", "EURJPY=X": "Euro / Japanischer Yen",
    "EURCHF=X": "Euro / Schweizer Franken", "GBPJPY=X": "Britisches Pfund / Japanischer Yen", "AUDJPY=X": "Australischer Dollar / Japanischer Yen",
    "CHFJPY=X": "Schweizer Franken / Japanischer Yen", "EURNZD=X": "Euro / Neuseeland-Dollar", "USDNOK=X": "US-Dollar / Norwegische Krone",
    "USDDKK=X": "US-Dollar / Dänische Krone", "USDSEK=X": "US-Dollar / Schwedische Krone", "USDTRY=X": "US-Dollar / Türkische Lira",
    "USDMXN=X": "US-Dollar / Mexikanischer Peso", "USDCNH=X": "US-Dollar / Chinesischer Yuan", "GBPAUD=X": "Britisches Pfund / Australischer Dollar",
    "EURAUD=X": "Euro / Australischer Dollar", "EURCAD=X": "Euro / Kanadischer Dollar",
    # Edelmetalle & Rohstoffe
    "XAUUSD": "Gold", "XAGUSD": "Silber", "XPTUSD": "Platin", "XPDUSD": "Palladium", "WTI": "Rohöl (West Texas)", "BRENT": "Brent-Öl",
    "NG=F": "Erdgas", "HG=F": "Kupfer", "SI=F": "Silber (Futures)", "GC=F": "Gold (Futures)", "CL=F": "Crude Oil (Futures)",
    "PL=F": "Platin (Futures)", "PA=F": "Palladium (Futures)", "ZC=F": "Mais (Futures)", "ZS=F": "Sojabohnen (Futures)",
    "ZR=F": "Weizen (Futures)", "KC=F": "Kaffee", "SB=F": "Zucker", "CT=F": "Baumwolle",
    # Indizes
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "Nasdaq 100", "^GDAXI": "DAX 40", "^FCHI": "CAC 40", "^FTSE": "FTSE 100",
    "^N225": "Nikkei 225", "^HSI": "Hang Seng (Hong Kong)", "000001.SS": "Shanghai Composite", "^BVSP": "Bovespa",
    "^GSPTSE": "TSX Kanada", "^SSMI": "SMI Schweiz", "^AS51": "ASX 200 Australien", "^MXX": "IPC Mexiko", "^STOXX50E": "Euro Stoxx 50",
    "^IBEX": "IBEX 35 Spanien", "^NSEI": "Nifty 50 Indien",
    # Kryptowährungen
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin", "SOL-USD": "Solana", "XRP-USD": "Ripple",
    "ADA-USD": "Cardano", "DOGE-USD": "Dogecoin", "DOT-USD": "Polkadot", "AVAX-USD": "Avalanche", "LTC-USD": "Litecoin",
    "TRX-USD": "Tron", "LINK-USD": "Chainlink", "ATOM-USD": "Cosmos", "MATIC-USD": "Polygon", "UNI-USD": "Uniswap",
    "EOS-USD": "EOS", "FTT-USD": "FTX Token", "ALGO-USD": "Algorand", "XTZ-USD": "Tezos", "NEO-USD": "NEO",
    "AAVE-USD": "Aave", "COMP-USD": "Compound", "MKR-USD": "Maker", "SUSHI-USD": "SushiSwap", "FIL-USD": "Filecoin",
    "ICP-USD": "Internet Computer", "LUNA-USD": "Terra", "CEL-USD": "Celsius", "RVN-USD": "Ravencoin", "KSM-USD": "Kusama",
    "ENJ-USD": "Enjin Coin", "CHZ-USD": "Chiliz"
}

# --- Assets aus prognose.txt ---
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

# --- Candlestick-Erkennung ---
def detect_candlestick(df):
    if len(df) < 3:
        return "Neutral", "up", 50.0

    df = df.copy()
    df['Body'] = df['Close'] - df['Open']
    df['Range'] = df['High'] - df['Low']

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    # --- float-Konvertierung für Pandas Series ---
    def to_float(val):
        return float(val.iloc[0]) if isinstance(val, pd.Series) else float(val)

    last_body = to_float(last['Body'])
    prev_body = to_float(prev['Body'])
    prev2_body = to_float(prev2['Body'])
    last_open = to_float(last['Open'])
    last_close = to_float(last['Close'])
    last_high = to_float(last['High'])
    last_low = to_float(last['Low'])
    prev_close = to_float(prev['Close'])
    prev_open = to_float(prev['Open'])
    prev2_open = to_float(prev2['Open'])
    prev2_close = to_float(prev2['Close'])
    last_range = to_float(last['Range'])

    pattern = "Neutral"
    trend = "up"

    # --- Mustererkennung ---
    if prev_body < 0 and last_body > 0 and abs(last_body) > abs(prev_body):
        pattern = "Bullish Engulfing"
        trend = "up"
    elif prev_body > 0 and last_body < 0 and abs(last_body) > abs(prev_body):
        pattern = "Bearish Engulfing"
        trend = "down"
    elif last_range > 0 and last_body / last_range < 0.3 and (last_close - last_low)/last_range > 0.6:
        pattern = "Hammer/Hanging Man"
        trend = "up" if last_close > last_open else "down"
    elif last_range > 0 and last_body / last_range < 0.3 and (last_high - last_close)/last_range > 0.6:
        pattern = "Inverted Hammer / Shooting Star"
        trend = "up" if last_close > last_open else "down"
    elif last_range > 0 and abs(last_body)/last_range < 0.1:
        pattern = "Doji"
        trend = "neutral"
    elif prev_body < 0 and last_body > 0 and last_open < prev_close and last_close > prev_close*0.5:
        pattern = "Piercing Line"
        trend = "up"
    elif prev_body > 0 and last_body < 0 and last_open > prev_close and last_close < prev_close*0.5:
        pattern = "Dark Cloud Cover"
        trend = "down"
    elif prev2_body > 0 and prev_body > 0 and last_body > 0:
        pattern = "Three White Soldiers"
        trend = "up"
    elif prev2_body < 0 and prev_body < 0 and last_body < 0:
        pattern = "Three Black Crows"
        trend = "down"
    elif last_range > 0 and abs(last_body)/last_range < 0.3 and 0.3 < (last_close - last_low)/last_range < 0.7:
        pattern = "Spinning Top"
        trend = "neutral"
    else:
        trend = "up" if last_close > last_open else "down"

    confidence = max(min(abs(last_body)/last_range * 100 * 0.8, 80), 5)
    return pattern, trend, round(confidence, 2)

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

# --- Alles analysieren ---
def analyze_and_predict_all():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        if df is None:
            continue
        pattern, trend, confidence = detect_candlestick(df)
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "trend": trend,
            "confidence": confidence,
            "df": df
        })
    top_up = sorted([r for r in results if r['trend']=='up' and r['pattern']!="Neutral"], key=lambda x:x['confidence'], reverse=True)[:5]
    top_down = sorted([r for r in results if r['trend']=='down' and r['pattern']!="Neutral"], key=lambda x:x['confidence'], reverse=True)[:5]
    return top_up, top_down
