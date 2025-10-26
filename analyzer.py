import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# --- Asset-Langnamen ---
ASSETS = {
    # Währungen
    "EURUSD=X": "Euro / US-Dollar",
    "USDJPY=X": "US-Dollar / Japanischer Yen",
    "GBPUSD=X": "Britisches Pfund / US-Dollar",
    "AUDUSD=X": "Australischer Dollar / US-Dollar",
    "USDCAD=X": "US-Dollar / Kanadischer Dollar",
    "USDCHF=X": "US-Dollar / Schweizer Franken",
    "NZDUSD=X": "Neuseeländischer Dollar / US-Dollar",
    "EURGBP=X": "Euro / Britisches Pfund",
    "EURJPY=X": "Euro / Japanischer Yen",
    "EURCHF=X": "Euro / Schweizer Franken",
    "GBPJPY=X": "Britisches Pfund / Japanischer Yen",
    "AUDJPY=X": "Australischer Dollar / Japanischer Yen",
    "CHFJPY=X": "Schweizer Franken / Japanischer Yen",
    "EURNZD=X": "Euro / Neuseeländischer Dollar",
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
    "^HSI": "Hang Seng",
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

def fetch_data(ticker, period="30d", interval="1d"):
    """Historische Kursdaten abrufen"""
    df = yf.download(ticker, period=period, interval=interval)
    df = df.dropna()
    return df

def bullish_bearish_engulfing(df):
    """Candlestick Engulfing Pattern erkennen"""
    last = df.iloc[-1]
    prev = df.iloc[-2]
    # Bullish Engulfing
    if (last['Close'] > last['Open']) and (prev['Close'] < prev['Open']) and (last['Open'] < prev['Close']) and (last['Close'] > prev['Open']):
        return "Bullish Engulfing"
    # Bearish Engulfing
    elif (last['Close'] < last['Open']) and (prev['Close'] > prev['Open']) and (last['Open'] > prev['Close']) and (last['Close'] < prev['Open']):
        return "Bearish Engulfing"
    else:
        return None

def calculate_trend_confidence(df):
    """Einfacher Trend und Confidence berechnen"""
    returns = df['Close'].pct_change().dropna()
    mean_return = returns.mean()
    std_return = returns.std()
    trend = "Uptrend" if mean_return > 0 else "Downtrend"
    confidence = min(max(abs(mean_return)/std_return,0),1)  # normiert auf 0-1
    return trend, round(confidence,2)

def generate_chart(df, ticker):
    """Chart mit Preisverlauf erzeugen"""
    plt.figure(figsize=(6,4))
    plt.plot(df.index, df['Close'], label="Close", color='blue')
    plt.title(f"{ASSETS.get(ticker, ticker)} Kursverlauf")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.tight_layout()
    filename = f"charts/{ticker.replace('=','').replace('-','')}.png"
    os.makedirs("charts", exist_ok=True)
    plt.savefig(filename)
    plt.close()
    return filename

def analyze_ticker(ticker):
    df = fetch_data(ticker)
    pattern = bullish_bearish_engulfing(df)
    trend, confidence = calculate_trend_confidence(df)
    chart_path = generate_chart(df, ticker)
    return {
        "ticker": ticker,
        "name": ASSETS.get(ticker, ticker),
        "trend": trend,
        "pattern": pattern,
        "confidence": confidence,
        "chart": chart_path
    }

def analyze_all():
    results = []
    for ticker in ASSETS.keys():
        try:
            res = analyze_ticker(ticker)
            results.append(res)
        except Exception as e:
            print(f"Fehler bei {ticker}: {e}")
    return results

if __name__ == "__main__":
    analysis = analyze_all()
    # Optional in CSV speichern
    pd.DataFrame(analysis).to_csv("analysis_results.csv", index=False)
    print("Analyse abgeschlossen!")
