# prognose_to_discord.py
import json
import os
import requests

# Webhook aus GitHub Secrets
WEBHOOK_URL = os.environ.get("PROGNOSE_WEBHOOK")

# Pfad zu den bereits ausgewerteten Daten von analyzer.py
DATA_FILE = "prognose_results.json"

# Mapping für ausgeschriebene Asset-Namen
ASSET_NAMES = {
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

def build_embed(results):
    # Sortiere nach Confidence
    results_sorted = sorted(results, key=lambda x: x['confidence'], reverse=True)

    # Nur Top 10 Aufwärts/Abwärts
    up = [r for r in results_sorted if r['direction'] == "up"][:10]
    down = [r for r in results_sorted if r['direction'] == "down"][:10]

    embed = {
        "username": "📊 Top-Picks Chart-Pattern Analyse",
        "embeds": [
            {
                "title": "Aufwärtspatterns 🔼",
                "description": "\n".join([f"**{ASSET_NAMES.get(r['symbol'], r['symbol'])} ({r['symbol']}):** {', '.join(r['patterns'])} | `{r['confidence']:.2f}`" for r in up]),
                "color": 3066993  # Grün
            },
            {
                "title": "Abwärtspatterns 🔽",
                "description": "\n".join([f"**{ASSET_NAMES.get(r['symbol'], r['symbol'])} ({r['symbol']}):** {', '.join(r['patterns'])} | `{r['confidence']:.2f}`" for r in down]),
                "color": 15158332  # Rot
            }
        ]
    }
    return embed

def post_to_discord():
    # Lade die bereits ausgewerteten Daten
    with open(DATA_FILE, "r") as f:
        results = json.load(f)

    embed = build_embed(results)
    response = requests.post(WEBHOOK_URL, json=embed)

    if response.status_code == 204 or response.status_code == 200:
        print("✅ Prognose erfolgreich an Discord gesendet!")
    else:
        print(f"❌ Fehler beim Senden: {response.status_code} - {response.text}")

if __name__ == "__main__":
    post_to_discord()
