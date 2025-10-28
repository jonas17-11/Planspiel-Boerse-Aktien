import yfinance as yf
import pandas as pd
import numpy as np

# --- Mapping Ticker -> Ausgeschriebener Name ---
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
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

# --- Candlestick-Erkennung ---
def detect_candlestick(df):
    if len(df) < 3:  # Für Patterns wie Morning/Evening Star brauchen wir 3 Kerzen
        return "Neutral", None, None

    df = df.copy()
    df['Body'] = df['Close'] - df['Open']
    df['Range'] = df['High'] - df['Low']

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    last_body = float(last['Body'])
    prev_body = float(prev['Body'])
    prev2_body = float(prev2['Body'])

    last_close = float(last['Close'])
    last_open = float(last['Open'])
    last_high = float(last['High'])
    last_low = float(last['Low'])
    last_range = float(last['Range']) if float(last['Range']) != 0 else 1e-8

    pattern = "Neutral"
    trend = None
    confidence = None

    # --- Einfachere Patterns ---
    if prev_body < 0 and last_body > 0 and abs(last_body) > abs(prev_body):
        pattern = "Bullish Engulfing"
        trend = "up"
    elif prev_body > 0 and last_body < 0 and abs(last_body) > abs(prev_body):
        pattern = "Bearish Engulfing"
        trend = "down"
    elif last_body / last_range < 0.3 and (last_high - last_open) / last_range > 0.6 and (last_close - last_low) / last_range > 2 * abs(last_body) / last_range:
        pattern = "Hammer"
        trend = "up"
    elif last_body / last_range < 0.3 and (last_high - last_close) / last_range > 0.6 and (last_open - last_low) / last_range > 2 * abs(last_body) / last_range:
        pattern = "Inverted Hammer"
        trend = "down"
    elif abs(last_body) / last_range < 0.1:
        pattern = "Doji"
        trend = None

    # --- Mehrtages-Patterns ---
    # Morning Star
    if prev2_body < 0 and abs(prev_body) / prev_body < 0.3 and last_body > 0 and last_close > prev2_open := float(prev2['Open']):
        pattern = "Morning Star"
        trend = "up"
    # Evening Star
    if prev2_body > 0 and abs(prev_body) / prev_body < 0.3 and last_body < 0 and last_close < prev2_open:
        pattern = "Evening Star"
        trend = "down"
    # Hanging Man
    if prev_body > 0 and last_body / last_range < 0.3 and (last_close - last_low)/last_range < 0.25:
        pattern = "Hanging Man"
        trend = "down"
    # Shooting Star
    if prev_body < 0 and last_body / last_range < 0.3 and (last_high - last_close)/last_range > 0.6:
        pattern = "Shooting Star"
        trend = "down"

    if trend is not None:
        confidence = min(abs(last_body) / last_open * 100 * 2, 100)
        confidence = round(confidence, 2)

    return pattern, trend, confidence

# --- Daten laden ---
def fetch_data(ticker, period="1mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

# --- Alles analysieren ---
def analyze_and_predict_all():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        if df is None or df.empty:
            continue
        pattern, trend, confidence = detect_candlestick(df)
        if trend is None or pattern == "Neutral":
            continue
        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "trend": trend,
            "confidence": confidence,
            "df": df
        })
    top_up = sorted([r for r in results if r['trend']=='up'], key=lambda x:x['confidence'], reverse=True)
    top_down = sorted([r for r in results if r['trend']=='down'], key=lambda x:x['confidence'], reverse=True)
    return top_up, top_down
