import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# --- Mapping Ticker -> Ausgeschriebener Name ---
ASSET_NAMES = {
    # Währungen (Forex)
    "EURUSD": "Euro / US-Dollar",
    "USDJPY": "US-Dollar / Japanischer Yen",
    "GBPUSD": "Britisches Pfund / US-Dollar",
    "AUDUSD": "Australischer Dollar / US-Dollar",
    "USDCAD": "US-Dollar / Kanadischer Dollar",
    "USDCHF": "US-Dollar / Schweizer Franken",
    "NZDUSD": "Neuseeland-Dollar / US-Dollar",
    "EURGBP": "Euro / Britisches Pfund",
    "EURJPY": "Euro / Japanischer Yen",
    "EURCHF": "Euro / Schweizer Franken",
    "GBPJPY": "Britisches Pfund / Japanischer Yen",
    "AUDJPY": "Australischer Dollar / Japanischer Yen",
    "CHFJPY": "Schweizer Franken / Japanischer Yen",
    "EURNZD": "Euro / Neuseeland-Dollar",
    "USDNOK": "US-Dollar / Norwegische Krone",
    "USDDKK": "US-Dollar / Dänische Krone",
    "USDSEK": "US-Dollar / Schwedische Krone",
    "USDTRY": "US-Dollar / Türkische Lira",
    "USDMXN": "US-Dollar / Mexikanischer Peso",
    "USDCNH": "US-Dollar / Chinesischer Yuan",
    "GBPAUD": "Britisches Pfund / Australischer Dollar",
    "EURAUD": "Euro / Australischer Dollar",
    "EURCAD": "Euro / Kanadischer Dollar",
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

# Ordner für Charts
os.makedirs("charts", exist_ok=True)

def fetch_data(ticker, period="1mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

def analyze_pattern(df):
    if df is None or df.empty:
        return None, 0

    start = df['Close'].iloc[0]
    end = df['Close'].iloc[-1]
    change = (end - start) / start

    if change > 0.02:
        return "Aufwärts-Trend 📈", round(change*100, 2)
    elif change < -0.02:
        return "Abwärts-Trend 📉", round(change*100, 2)
    else:
        return "Seitwärts-Trend ➖", round(change*100, 2)

def generate_chart(ticker, df):
    plt.figure(figsize=(6,3))
    plt.plot(df['Close'], label='Schlusskurs', color='royalblue', linewidth=2)
    plt.title(f"{ASSET_NAMES.get(ticker, ticker)}")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.grid(True, linestyle="--", alpha=0.5)
    chart_path = f"charts/chart_{ticker.replace('/','_')}.png"
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    return chart_path

def get_analysis():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        pattern, confidence = analyze_pattern(df)
        if pattern:
            chart_path = generate_chart(ticker, df) if df is not None else None
            results.append({
                "ticker": ticker,
                "name": ASSET_NAMES.get(ticker, ticker),
                "pattern": pattern,
                "confidence": confidence,
                "chart": chart_path
            })
    return results

if __name__ == "__main__":
    analysis = get_analysis()
    for a in analysis:
        print(f"{a['name']}: {a['pattern']} ({a['confidence']}%) | Chart: {a['chart']}")
