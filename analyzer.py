import yfinance as yf
import pandas as pd

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

# --- Assets aus prognose.txt laden ---
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

# --- Candlestick-Erkennung ---
def detect_candlestick(df):
    if len(df) < 2:
        return "Neutral", "neutral", 0.0

    df = df.copy()
    df['Body'] = df['Close'] - df['Open']
    df['Range'] = df['High'] - df['Low']
    last = df.iloc[-1]
    prev = df.iloc[-2]

    last_open = float(last['Open'])
    last_close = float(last['Close'])
    last_high = float(last['High'])
    last_low = float(last['Low'])
    last_body = last_close - last_open
    prev_body = float(prev['Close']) - float(prev['Open'])

    pattern = "Neutral"
    trend = "neutral"
    confidence = 0.0

    # Bullish Engulfing
    if prev_body < 0 < last_body and abs(last_body) > abs(prev_body):
        pattern = "Bullish Engulfing"
        trend = 'up'
        confidence = min(abs(last_body) / last['Close'] * 100 * 0.8, 90)
    # Bearish Engulfing
    elif prev_body > 0 > last_body and abs(last_body) > abs(prev_body):
        pattern = "Bearish Engulfing"
        trend = 'down'
        confidence = min(abs(last_body) / last['Close'] * 100 * 0.8, 90)
    # Hammer
    elif last_body > 0 and (last_high - last_close) >= 2 * last_body and (last_close - last_low) <= 0.25 * last_body:
        pattern = "Hammer"
        trend = 'up'
        confidence = min(abs(last_body) / last['Close'] * 100 * 0.6, 80)
    # Shooting Star
    elif last_body < 0 and (last_high - last_open) >= 2 * abs(last_body) and (last_close - last_low) <= 0.25 * abs(last_body):
        pattern = "Shooting Star"
        trend = 'down'
        confidence = min(abs(last_body) / last['Close'] * 100 * 0.6, 80)
    # Doji
    elif abs(last_body) <= 0.1 * (last_high - last_low):
        pattern = "Doji"
        trend = "neutral"
        confidence = min((abs(last_body)/(last_high-last_low))*100, 50)
    # Keine klare Kerze
    else:
        pattern = "Neutral"
        trend = 'up' if last_close > last_open else 'down'
        confidence = min(abs(last_body)/(last_high-last_low)*100, 50)

    return pattern, trend, round(confidence,2)

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
        if pattern == "Neutral":
            continue  # Neutral ausblenden
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
