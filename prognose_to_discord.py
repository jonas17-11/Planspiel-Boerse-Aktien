import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests
import matplotlib.dates as mdates

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_candlestick_subplot(ax, df, trend_up=True, pattern="", confidence=0, y_min=None, y_max=None):
    """Zeichnet ein Candlestick-Subplot für einen Asset"""
    df_plot = df.copy()
    df_plot['Date'] = df_plot.index
    width = 0.4

    for idx, row in df_plot.iterrows():
        try:
            open_price = float(row['Open'].item() if hasattr(row['Open'], 'item') else row['Open'])
            close_price = float(row['Close'].item() if hasattr(row['Close'], 'item') else row['Close'])
            high_price = float(row['High'].item() if hasattr(row['High'], 'item') else row['High'])
            low_price = float(row['Low'].item() if hasattr(row['Low'], 'item') else row['Low'])
        except (ValueError, TypeError):
            continue

        color = 'green' if close_price >= open_price else 'red'
        ax.plot([idx, idx], [low_price, high_price], color='black', linewidth=1)
        ax.add_patch(plt.Rectangle(
            (mdates.date2num(idx)-width/2, min(open_price, close_price)),
            width,
            abs(close_price - open_price),
            color=color
        ))

    # Einfache lineare Prognose
    y_last = float(df_plot['Close'].values[-1])
    factor = 1 + (confidence/100)*0.05
    forecast_y = np.linspace(y_last, y_last*factor if trend_up else y_last/factor, 5)
    forecast_dates = pd.date_range(start=df_plot.index[-1], periods=6, freq='D')[1:]
    ax.plot(forecast_dates, forecast_y, linestyle='--', color='green' if trend_up else 'red', linewidth=2)

    ax.set_ylabel("Preis")
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.set_title(f"{pattern} ({confidence}%)", fontsize=10)

    if y_min is not None and y_max is not None:
        ax.set_ylim(float(y_min), float(y_max))  # unbedingt float() verwenden

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

    # Berechne gemeinsame Y-Achse für alle Subplots
    all_prices = pd.concat([a['df']['Close'] for a in all_assets])
    y_min = all_prices.min()
    y_max = all_prices.max()

    # Alle Assets in einem Bild untereinander
    num_assets = len(all_assets)
    fig, axes = plt.subplots(num_assets, 1, figsize=(12, 4*num_assets), constrained_layout=True)

    if num_assets == 1:
        axes = [axes]  # damit es iterierbar bleibt

    for ax, a in zip(axes, all_assets):
        plot_candlestick_subplot(ax, a['df'], trend_up=(a['trend']=="up"),
                                 pattern=a['pattern'], confidence=a['confidence'],
                                 y_min=y_min, y_max=y_max)
        ax.set_title(f"{a['name']} - {a['pattern']} ({a['confidence']}%)", fontsize=12)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    files = [("file", ("all_assets.png", buf, "image/png"))]

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    
    if response.status_code in (200,204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
