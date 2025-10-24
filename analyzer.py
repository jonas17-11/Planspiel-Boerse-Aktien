import json
import random
from datetime import datetime

# Mapping von Tickers zu ausgeschriebenen Namen
ASSET_NAMES = {
    # Forex
    "EURUSD": "Euro / US-Dollar", "USDJPY": "US-Dollar / Japanischer Yen", "GBPUSD": "Britisches Pfund / US-Dollar",
    "AUDUSD": "Australischer Dollar / US-Dollar", "USDCAD": "US-Dollar / Kanadischer Dollar", "USDCHF": "US-Dollar / Schweizer Franken",
    "NZDUSD": "Neuseeland-Dollar / US-Dollar", "EURGBP": "Euro / Britisches Pfund", "EURJPY": "Euro / Japanischer Yen",
    "EURCHF": "Euro / Schweizer Franken", "GBPJPY": "Britisches Pfund / Japanischer Yen", "AUDJPY": "Australischer Dollar / Japanischer Yen",
    "CHFJPY": "Schweizer Franken / Japanischer Yen", "EURNZD": "Euro / Neuseeland-Dollar", "USDNOK": "US-Dollar / Norwegische Krone",
    "USDDKK": "US-Dollar / Dänische Krone", "USDSEK": "US-Dollar / Schwedische Krone", "USDTRY": "US-Dollar / Türkische Lira",
    "USDMXN": "US-Dollar / Mexikanischer Peso", "USDCNH": "US-Dollar / Chinesischer Yuan", "GBPAUD": "Britisches Pfund / Australischer Dollar",
    "EURAUD": "Euro / Australischer Dollar", "EURCAD": "Euro / Kanadischer Dollar",

    # Edelmetalle & Rohstoffe
    "XAUUSD": "Gold", "XAGUSD": "Silber", "XPTUSD": "Platin", "XPDUSD": "Palladium",
    "WTI": "Rohöl (WTI)", "BRENT": "Brent-Öl", "NG=F": "Erdgas", "HG=F": "Kupfer",
    "SI=F": "Silber (Futures)", "GC=F": "Gold (Futures)", "CL=F": "Crude Oil (Futures)",
    "PL=F": "Platin (Futures)", "PA=F": "Palladium (Futures)", "ZC=F": "Mais (Futures)",
    "ZS=F": "Sojabohnen (Futures)", "ZR=F": "Weizen (Futures)", "KC=F": "Kaffee",
    "SB=F": "Zucker", "CT=F": "Baumwolle",

    # Indizes
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "Nasdaq 100", "^GDAXI": "DAX 40",
    "^FCHI": "CAC 40", "^FTSE": "FTSE 100", "^N225": "Nikkei 225", "^HSI": "Hang Seng",
    "000001.SS": "Shanghai Composite", "^BVSP": "Bovespa", "^GSPTSE": "TSX Kanada",
    "^SSMI": "SMI Schweiz", "^AS51": "ASX 200 Australien", "^MXX": "IPC Mexiko",
    "^STOXX50E": "Euro Stoxx 50", "^IBEX": "IBEX 35 Spanien", "^NSEI": "Nifty 50 Indien",

    # Kryptowährungen
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin", "SOL-USD": "Solana",
    "XRP-USD": "Ripple", "ADA-USD": "Cardano", "DOGE-USD": "Dogecoin", "DOT-USD": "Polkadot",
    "AVAX-USD": "Avalanche", "LTC-USD": "Litecoin", "TRX-USD": "Tron", "LINK-USD": "Chainlink",
    "ATOM-USD": "Cosmos", "MATIC-USD": "Polygon", "UNI-USD": "Uniswap", "EOS-USD": "EOS",
    "FTT-USD": "FTX Token", "ALGO-USD": "Algorand", "XTZ-USD": "Tezos", "NEO-USD": "NEO",
    "AAVE-USD": "Aave", "COMP-USD": "Compound", "MKR-USD": "Maker", "SUSHI-USD": "SushiSwap",
    "FIL-USD": "Filecoin", "ICP-USD": "Internet Computer", "LUNA-USD": "Terra", "CEL-USD": "Celsius",
    "RVN-USD": "Ravencoin", "KSM-USD": "Kusama", "ENJ-USD": "Enjin Coin", "CHZ-USD": "Chiliz"
}

# Dummy-Funktion zur Simulation von Chart-Pattern Analyse
def generate_dummy_analysis(ticker):
    patterns = ["Head and Shoulders", "Double Top", "Double Bottom", "Rising Wedge", "Falling Wedge",
                "Triangle", "Rectangle", "Cup and Handle", "Bullish Flag", "Bearish Flag", "Inverse Head and Shoulders"]
    top_patterns = random.sample(patterns, k=random.randint(1, 3))
    confidence = round(random.uniform(0.6, 0.99), 2)
    return {"ticker": ticker, "name": ASSET_NAMES.get(ticker, ticker), "patterns": top_patterns, "confidence": confidence}

def analyze_assets():
    # Liste der Assets aus prognose.txt laden
    assets = []
    with open("prognose.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            ticker = line.split()[0]  # nur der Ticker, Kommentar ignorieren
            assets.append(ticker)

    results = [generate_dummy_analysis(t) for t in assets]
    return results

def save_results(results, filename="analysis_results.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"timestamp": str(datetime.utcnow()), "results": results}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    results = analyze_assets()
    save_results(results)
    print("✅ Analyse abgeschlossen und gespeichert in 'analysis_results.json'")
