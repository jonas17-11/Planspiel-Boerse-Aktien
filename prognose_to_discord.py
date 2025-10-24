import datetime
from analyzer import run_analysis_patterns
import requests

# Mapping für lesbare Namen der Assets
ASSET_NAMES = {
    # Forex
    "EURUSD": "EUR/USD", "USDJPY": "USD/JPY", "GBPUSD": "GBP/USD", "AUDUSD": "AUD/USD",
    "USDCAD": "USD/CAD", "USDCHF": "USD/CHF", "NZDUSD": "NZD/USD", "EURGBP": "EUR/GBP",
    "EURJPY": "EUR/JPY", "EURCHF": "EUR/CHF", "GBPJPY": "GBP/JPY", "AUDJPY": "AUD/JPY",
    "CHFJPY": "CHF/JPY", "EURNZD": "EUR/NZD", "USDNOK": "USD/NOK", "USDDKK": "USD/DKK",
    "USDSEK": "USD/SEK", "USDTRY": "USD/TRY", "USDMXN": "USD/MXN", "USDCNH": "USD/CNH",
    "GBPAUD": "GBP/AUD", "EURAUD": "EUR/AUD", "EURCAD": "EUR/CAD",

    # Edelmetalle & Rohstoffe
    "XAUUSD": "Gold", "XAGUSD": "Silber", "XPTUSD": "Platin", "XPDUSD": "Palladium",
    "WTI": "Rohöl WTI", "BRENT": "Brent-Öl", "NG=F": "Erdgas", "HG=F": "Kupfer",
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
    "FIL-USD": "Filecoin", "ICP-USD": "Internet Computer", "LUNA-USD": "Terra",
    "CEL-USD": "Celsius", "RVN-USD": "Ravencoin", "KSM-USD": "Kusama",
    "ENJ-USD": "Enjin Coin", "CHZ-USD": "Chiliz"
}

DISCORD_WEBHOOK_URL = "DEIN_DISCORD_WEBHOOK_HIER"

def confidence_emoji(conf):
    if conf >= 0.90:
        return "🟢"
    elif conf >= 0.80:
        return "🟡"
    elif conf >= 0.70:
        return "🟠"
    else:
        return "🔴"

def build_embed():
    results = run_analysis_patterns()
    results_sorted = sorted(results, key=lambda x: x['confidence'], reverse=True)

    top_up = [r for r in results_sorted if r['direction'] == 'up'][:10]
    top_down = [r for r in results_sorted if r['direction'] == 'down'][:10]

    now = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M Uhr UTC")

    embed = {
        "title": f"📊 Top-Picks Chart-Pattern Analyse",
        "description": f"**Höchste Wahrscheinlichkeit** ({now})",
        "color": 0x1ABC9C,
        "fields": [],
        "footer": {"text": "Nur die Top 10 Auf- und Abwärtspatterns"}
    }

    # Aufwärts
    up_text = ""
    for r in top_up:
        symbol_name = ASSET_NAMES.get(r['symbol'], r['symbol'])
        patterns = ", ".join(r['patterns'])
        emoji = confidence_emoji(r['confidence'])
        up_text += f"{emoji} **{r['symbol']} {symbol_name}**\n   {patterns} | {r['confidence']:.2f}\n\n"
    embed['fields'].append({
        "name": "📈 Aufwärtspatterns",
        "value": up_text or "Keine Daten verfügbar",
        "inline": False
    })

    # Abwärts
    down_text = ""
    for r in top_down:
        symbol_name = ASSET_NAMES.get(r['symbol'], r['symbol'])
        patterns = ", ".join(r['patterns'])
        emoji = confidence_emoji(r['confidence'])
        down_text += f"{emoji} **{r['symbol']} {symbol_name}**\n   {patterns} | {r['confidence']:.2f}\n\n"
    embed['fields'].append({
        "name": "📉 Abwärtspatterns",
        "value": down_text or "Keine Daten verfügbar",
        "inline": False
    })

    return embed

def post_to_discord():
    embed = build_embed()
    payload = {"embeds": [embed]}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code in (200, 204):
        print("📤 Nachricht erfolgreich an Discord gesendet!")
    else:
        print(f"❌ Fehler beim Senden an Discord: {response.status_code}, {response.text}")

if __name__ == "__main__":
    print("📤 Sende Top-Picks Chart-Pattern Prognose an Discord...")
    post_to_discord()
