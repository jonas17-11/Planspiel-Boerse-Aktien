import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import os

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
    # Weitere Assets hier...
}

# Assets aus prognose.txt
with open("prognose.txt", "r") as f:
    assets = [line.split()[0] for line in f if line.strip() and not line.startswith("#")]

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
    if df is None or df.empty or 'Close' not in df.columns:
        return None, 0

    start = df['Close'].iloc[0]
    end = df['Close'].iloc[-1]

    if pd.isna(start) or pd.isna(end):
        return None, 0

    change = float((end - start) / start)

    if change > 0.02:
        return "Aufwärts-Trend 📈", round(change*100,2)
    elif change < -0.02:
        return "Abwärts-Trend 📉", round(change*100,2)
    else:
        return "Seitwärts-Trend ➖", round(change*100,2)

def plot_asset(df, ticker):
    plt.figure(figsize=(8,4))
    plt.plot(df.index, df['Close'], marker='o', linestyle='-', color='blue')
    plt.title(f"{ASSET_NAMES.get(ticker,ticker)} - Kursverlauf")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.grid(True)
    # Speichern als Bild
    filename = f"charts/{ticker}.png"
    os.makedirs("charts", exist_ok=True)
    plt.savefig(filename)
    plt.close()
    return filename

def get_analysis():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        pattern, confidence = analyze_pattern(df)
        chart_file = plot_asset(df, ticker) if df is not None else None
        if pattern:
            results.append({
                "ticker": ticker,
                "name": ASSET_NAMES.get(ticker,ticker),
                "pattern": pattern,
                "confidence": confidence,
                "chart": chart_file
            })
    return results

if __name__ == "__main__":
    analysis = get_analysis()
    for a in analysis:
        print(f"{a['name']}: {a['pattern']} ({a['confidence']}%) - Chart: {a['chart']}")
