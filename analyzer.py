import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import timedelta

# --- Assets aus prognose.txt laden ---
def load_assets(filename="prognose.txt"):
    assets = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            assets.append(line.split()[0])
    return assets

ASSET_NAMES = {}
with open("prognose.txt", "r", encoding="utf-8") as f:
    for line in f:
        if "#" in line and not line.strip().startswith("#"):
            parts = line.split("#")
            ticker = parts[0].strip()
            name = parts[1].strip()
            ASSET_NAMES[ticker] = name
        elif line.strip() and not line.startswith("#"):
            ASSET_NAMES[line.strip()] = line.strip()

assets = load_assets()

# --- Kursdaten laden ---
def fetch_data(ticker, period="3mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

# --- Patternanalyse + Prognose ---
def analyze_and_predict(df, days_ahead=5):
    if df is None or len(df) < 30:
        return None, None, None, None, None

    df = df.copy()
    df["t"] = np.arange(len(df))
    X = df[["t"]]
    y = df["Close"]

    model = LinearRegression()
    model.fit(X, y)

    trend = float(model.coef_[0])
    predicted_values = model.predict([[len(df) + i] for i in range(days_ahead)]).flatten()

    # SMA-basierte Pattern-Erkennung
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()

    # Letzte Werte sicher extrahieren
    sma20 = df["SMA20"].iloc[-1] if not pd.isna(df["SMA20"].iloc[-1]) else df["Close"].iloc[-1]
    sma50 = df["SMA50"].iloc[-1] if not pd.isna(df["SMA50"].iloc[-1]) else df["Close"].iloc[-1]
    close = df["Close"].iloc[-1]

    # In float umwandeln (kompatibel mit künftigen Pandas)
    sma20, sma50, close = float(sma20), float(sma50), float(close)

    pattern = "Seitwärtsbewegung ➖"
    confidence = 50

    # --- Pattern-Erkennung ---
    if sma20 > sma50 and trend > 0:
        pattern = "Golden Cross ✨ (Aufwärtstrend bestätigt)"
        confidence = 88
    elif sma20 < sma50 and trend < 0:
        pattern = "Death Cross 💀 (Abwärtstrend bestätigt)"
        confidence = 88
    elif trend > 0 and close > sma20:
        pattern = "Möglicher Breakout 🚀"
        confidence = 78
    elif trend < 0 and close < sma20:
        pattern = "Möglicher Breakdown 🔻"
        confidence = 78

    # Prozentänderung berechnen
    change_percent = ((predicted_values[-1] - close) / close) * 100

    # Prognosedaten (jetzt flach & sicher)
    future_dates = [df.index[-1] + timedelta(days=i + 1) for i in range(days_ahead)]
    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted": predicted_values
    })
    forecast_df.set_index("Date", inplace=True)

    return pattern, confidence, change_percent, df, forecast_df

# --- Hauptfunktion ---
def get_analysis():
    results = []
    for ticker in assets:
        df = fetch_data(ticker)
        if df is None:
            continue

        pattern, confidence, change, df, forecast = analyze_and_predict(df)
        if pattern is None:
            continue

        results.append({
            "ticker": ticker,
            "name": ASSET_NAMES.get(ticker, ticker),
            "pattern": pattern,
            "confidence": confidence,
            "predicted_change": change,
            "df": df,
            "forecast": forecast
        })
    return results

if __name__ == "__main__":
    analysis = get_analysis()
    for a in analysis:
        print(f"{a['name']}: {a['pattern']} ({a['confidence']}%) → {a['predicted_change']:.2f}%")
