import yfinance as yf
import pandas as pd
import numpy as np

# Mapping Ticker -> Ausgeschriebener Name
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
    "EURCAD": "Euro / Kanadischer Dollar", "XAUUSD": "Gold", "XAGUSD": "Silber",
    "XPTUSD": "Platin", "XPDUSD": "Palladium", "WTI": "Rohöl (West Texas)",
    "BRENT": "Brent-Öl", "NG=F": "Erdgas", "HG=F": "Kupfer",
    "SI=F": "Silber (Futures)", "GC=F": "Gold (Futures)", "CL=F": "Crude Oil (Futures)",
    "PL=F": "Platin (Futures)", "PA=F": "Palladium (Futures)", "ZC=F": "Mais (Futures)",
    "ZS=F": "Sojabohnen (Futures)", "ZR=F": "Weizen (Futures)", "KC=F": "Kaffee",
    "SB=F": "Zucker", "CT=F": "Baumwolle", "^GSPC": "S&P 500", "^DJI": "Dow Jones",
    "^IXIC": "Nasdaq 100", "^GDAXI": "DAX 40", "^FCHI": "CAC 40", "^FTSE": "FTSE 100",
    "^N225": "Nikkei 225", "^HSI": "Hang Seng (Hong Kong)", "000001.SS": "Shanghai Composite",
    "^BVSP": "Bovespa", "^GSPTSE": "TSX Kanada", "^SSMI": "SMI Schweiz", "^AS51": "ASX 200 Australien",
    "^MXX": "IPC Mexiko", "^STOXX50E": "Euro Stoxx 50", "^IBEX": "IBEX 35 Spanien",
    "^NSEI": "Nifty 50 Indien", "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin",
    "SOL-USD": "Solana", "XRP-USD": "Ripple", "ADA-USD": "Cardano", "DOGE-USD": "Dogecoin",
    "DOT-USD": "Polkadot", "AVAX-USD": "Avalanche", "LTC-USD": "Litecoin", "TRX-USD": "Tron",
    "LINK-USD": "Chainlink", "ATOM-USD": "Cosmos", "MATIC-USD": "Polygon", "UNI-USD": "Uniswap",
    "EOS-USD": "EOS", "FTT-USD": "FTX Token", "ALGO-USD": "Algorand", "XTZ-USD": "Tezos",
    "NEO-USD": "NEO", "AAVE-USD": "Aave", "COMP-USD": "Compound", "MKR-USD": "Maker",
    "SUSHI-USD": "SushiSwap", "FIL-USD": "Filecoin", "ICP-USD": "Internet Computer",
    "LUNA-USD": "Terra", "CEL-USD": "Celsius", "RVN-USD": "Ravencoin", "KSM-USD": "Kusama",
    "ENJ-USD": "Enjin Coin", "CHZ-USD": "Chiliz"
}

# Assets aus prognose.txt laden
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

def fetch_data(ticker, period="1mo", interval="1h"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

def detect_candlestick_pattern(df):
    """
    Einfache Candlestick-Erkennung:
    - Aufwärts-Trend: letzte Kerze grün + letzte 3 Kerzen höher als vorher
    - Abwärts-Trend: letzte Kerze rot + letzte 3 Kerzen niedriger als vorher
    - Seitwärts: sonst
    """
    if df is None or df.empty:
        return "Keine Daten", 0.0

    closes = df['Close']
    opens = df['Open']

    last_close = closes.iloc[-1]
    last_open = opens.iloc[-1]

    # einfacher Trend
    change = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]

    if last_close > last_open and closes.iloc[-1] > closes.iloc[-4:].min():
        return "Aufwärts-Trend 📈", round(change*100, 2)
    elif last_close < last_open and closes.iloc[-1] < closes.iloc[-4:].max():
        return "Abwärts-Trend 📉", round(abs(change)*100, 2)
    else:
        return "Seitwärts-Trend ➖", round(abs(change)*100, 2)

def analyze_assets():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        pattern, confidence = detect_candlestick_pattern(df)
        if pattern != "Keine Daten":
            results.append({
                "ticker": ticker,
                "name": ASSET_NAMES.get(ticker, ticker),
                "pattern": pattern,
                "confidence": confidence,
                "df": df
            })
    # Sortieren
    top_up = sorted([r for r in results if "Aufwärts" in r["pattern"]],
                    key=lambda x: x["confidence"], reverse=True)[:10]
    top_down = sorted([r for r in results if "Abwärts" in r["pattern"]],
                      key=lambda x: x["confidence"], reverse=True)[:10]
    return top_up, top_down

if __name__ == "__main__":
    up, down = analyze_assets()
    print("Top 10 Steigende:")
    for r in up:
        print(f"{r['name']}: {r['pattern']} ({r['confidence']}%)")
    print("\nTop 10 Fallende:")
    for r in down:
        print(f"{r['name']}: {r['pattern']} ({r['confidence']}%)")
