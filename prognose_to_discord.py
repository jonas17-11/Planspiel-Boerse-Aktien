import os
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

# --- Candlestick Subplot für einzelne Axes ---
def plot_candlestick_subplot(ax, df, trend_up=True, pattern="", confidence=0, y_min=None, y_max=None):
    df_plot = df.copy().tail(30)  # letzte 30 Tage
    width = 0.6

    for i, row in enumerate(df_plot.itertuples()):
        open_price = float(row.Open)
        close_price = float(row.Close)
        high_price = float(row.High)
        low_price = float(row.Low)
        color = 'green' if close_price >= open_price else 'red'
        # Kerze
        ax.vlines(i, low_price, high_price, color=color, linewidth=1)
        ax.add_patch(plt.Rectangle((i-width/2, min(open_price, close_price)),
                                   width,
                                   abs(close_price - open_price),
                                   color=color))

    # Trendlinie (einfach linear)
    y = df_plot['Close'].values
    x = np.arange(len(y))
    coeffs = np.polyfit(x, y, 1)
    forecast_x = np.arange(len(y), len(y)+5)
    forecast_y = np.polyval(coeffs, forecast_x)
    forecast_dates = pd.date_range(start=df_plot.index[-1], periods=6, freq='D')[1:]
    ax.plot(range(len(y), len(y)+5), forecast_y, linestyle='--', color='green' if trend_up else 'red')

    ax.set_xlim(-1, len(y)+5)
    if y_min is not None and y_max is not None:
        ax.set_ylim(float(y_min), float(y_max))
    ax.set_xticks([])
    ax.set_ylabel("Preis")

# --- Discord Nachricht ---
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

# --- Hauptfunktion ---
def post_to_discord():
    top_up, top_down = analyze_and_predict_all()

    # Nur das stärkste Pattern pro Aktie
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

    # Gemeinsame Y-Achse
    all_prices = pd.concat([a['df']['Close'] for a in all_assets])
    y_min = float(all_prices.min().item())
    y_max = float(all_prices.max().item())

    # Alle Assets in einem Bild
    num_assets = len(all_assets)
    fig, axes = plt.subplots(num_assets, 1, figsize=(12, 4*num_assets), constrained_layout=True)
    if num_assets == 1:
        axes = [axes]

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
    try:
        response = requests.post(WEBHOOK_URL, data=payload, files=files)
        if response.status_code in (200,204):
            print("Erfolgreich in Discord gesendet ✅")
        else:
            print(f"Fehler beim Senden: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Fehler beim Senden an Discord: {e}")

if __name__ == "__main__":
    post_to_discord()
