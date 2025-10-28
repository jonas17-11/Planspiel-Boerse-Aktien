import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests
import matplotlib.dates as mdates
from scipy.interpolate import make_interp_spline

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_candlesticks(df, name, trend_up=True, forecast_days=5, pattern="", confidence=0):
    """Candlestick-Diagramm mit geglätteter Trendprognose und dynamischer Breite"""
    if df is None or df.empty:
        return None

    df_plot = df.copy()
    df_plot['Date'] = df_plot.index

    plt.figure(figsize=(10,4))
    ax = plt.gca()

    num_candles = len(df_plot)
    width = max(0.4, min(1.0, 10/num_candles))

    # Candlesticks
    for idx, row in df_plot.iterrows():
        try:
            open_price = float(row['Open'])
            close_price = float(row['Close'])
            high_price = float(row['High'])
            low_price = float(row['Low'])
        except (ValueError, TypeError):
            continue  # Skip invalid rows

        color = 'green' if close_price >= open_price else 'red'
        ax.plot([idx, idx], [low_price, high_price], color='black')  # Schatten
        ax.add_patch(plt.Rectangle(
            (mdates.date2num(idx)-width/2, min(open_price, close_price)),
            width,
            abs(close_price - open_price),
            color=color
        ))

    # Prognose
    y_last = float(df_plot['Close'].values[-1])
    factor = 1 + (confidence/100) * 0.05  # Max ±5% für 100% confidence
    if trend_up:
        forecast_y = np.linspace(y_last, y_last*factor, forecast_days)
    else:
        forecast_y = np.linspace(y_last, y_last/factor, forecast_days)

    forecast_dates = pd.date_range(start=df_plot.index[-1], periods=forecast_days+1, freq='D')[1:]

    # Glätten der Forecast-Linie
    x_numeric = np.arange(len(forecast_y))
    if len(x_numeric) >= 2:  # spline benötigt mind. 2 Punkte
        x_smooth = np.linspace(x_numeric.min(), x_numeric.max(), 50)
        spline = make_interp_spline(x_numeric, forecast_y, k=1)
        forecast_y_smooth = spline(x_smooth)
        forecast_dates_smooth = pd.date_range(start=forecast_dates[0], end=forecast_dates[-1], periods=50)
        ax.plot(forecast_dates_smooth, forecast_y_smooth, linestyle='--',
                color='green' if trend_up else 'red', label='Prognose', linewidth=2)
        symbol = "📈" if trend_up else "📉"
        ax.text(forecast_dates_smooth[-1], forecast_y_smooth[-1]*1.005, symbol, fontsize=16, ha='center')
    else:
        # Fallback: einfache Linie
        ax.plot(forecast_dates, forecast_y, linestyle='--', color='green' if trend_up else 'red', label='Prognose', linewidth=2)

    ax.set_title(f"{name} - {pattern} ({confidence}%)")
    ax.set_ylabel("Preis")
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def build_discord_message(top_up, top_down):
    message = ""
    if top_up:
        message += "**📈 Top Steigende Assets:**\n"
        for a in top_up:
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"
    if top_down:
        message += "\n**📉 Top Fallende Assets:**\n"
        for a in top_down:
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"
    return message

def post_to_discord():
    top_up, top_down = analyze_and_predict_all()

    # Nur Pattern mit höchster Confidence pro Asset
    def pick_best_pattern(lst):
        seen = set()
        result = []
        for a in sorted(lst, key=lambda x: x['confidence'], reverse=True):
            if a['ticker'] not in seen:
                result.append(a)
                seen.add(a['ticker'])
        return result

    top_up = pick_best_pattern(top_up)
    top_down = pick_best_pattern(top_down)

    all_assets = top_up + top_down
    if not all_assets:
        print("Keine relevanten Muster gefunden.")
        return

    message = build_discord_message(top_up, top_down)

    # Jeden Chart als separate Datei posten
    files = []
    for a in all_assets:
        buf = plot_candlesticks(a['df'], a['name'], trend_up=(a['trend']=="up"),
                                pattern=a['pattern'], confidence=a['confidence'])
        if buf is None:
            continue  # überspringe Assets ohne gültige Daten
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    if not files:
        print("Keine Charts zum Senden verfügbar.")
        return

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    
    if response.status_code in (200,204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
