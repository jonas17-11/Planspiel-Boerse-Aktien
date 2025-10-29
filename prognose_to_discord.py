import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

# --- Candlestick-Subplot-Funktion ---
def plot_candlestick_subplot(ax, df, name, trend_up=True, confidence=50):
    df_plot = df.copy()
    width = 0.3
    x_vals = np.arange(len(df_plot))

    for i, row in zip(x_vals, df_plot.itertuples(index=False)):
        open_price = float(getattr(row, 'Open', row[0]))
        high_price = float(getattr(row, 'High', row[1]))
        low_price = float(getattr(row, 'Low', row[2]))
        close_price = float(getattr(row, 'Close', row[3]))

        color = 'green' if close_price >= open_price else 'red'
        ax.add_patch(Rectangle((i - width/2, min(open_price, close_price)),
                               width, abs(open_price - close_price), color=color))
        ax.vlines(i, low_price, high_price, color=color, linewidth=1)

    ax.set_title(name, fontsize=12, weight='bold')
    ax.set_ylabel("Preis", fontsize=10)
    ax.set_xticks([])

    # --- Prognosepfeil + Linie ---
    y_top = df_plot['High'].max()
    y_bottom = df_plot['Low'].min()
    y_range = y_top - y_bottom
    if y_range == 0:
        y_range = 1

    slope = (confidence / 100) * (y_range * 0.3)  # je höher Confidence, desto steiler
    direction = 1 if trend_up else -1
    start_y = df_plot['Close'].iloc[-1]
    end_y = start_y + direction * slope

    base_color = np.array(to_rgba('green' if trend_up else 'red'))
    intensity = 0.4 + 0.6 * (confidence / 100)
    line_color = tuple(base_color[:3] * intensity) + (1.0,)

    ax.plot([len(df_plot)-1, len(df_plot)], [start_y, end_y],
            color=line_color, linewidth=2, linestyle='--', label=f"{'↑' if trend_up else '↓'} {confidence}%")

    ax.legend(loc='upper left', fontsize=8)

# --- Discord-Nachricht ---
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

# --- Alles analysieren & senden ---
def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    all_assets = top_up + top_down
    if not all_assets:
        print("Keine relevanten Muster gefunden.")
        return

    message = build_discord_message(top_up, top_down)
    n = len(all_assets)
    fig, axes = plt.subplots(n, 1, figsize=(12, 4*n), constrained_layout=True, dpi=300)

    if n == 1:
        axes = [axes]

    for ax, a in zip(axes, all_assets):
        plot_candlestick_subplot(ax, a['df'], a['name'],
                                 trend_up=(a['trend'] == "up"), confidence=a['confidence'])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300)
    plt.close()
    buf.seek(0)

    payload = {"content": message}
    files = [("file", ("top_assets.png", buf, "image/png"))]
    response = requests.post(WEBHOOK_URL, data=payload, files=files)

    if response.status_code in (200, 204):
        print("✅ Erfolgreich in Discord gesendet")
    else:
        print(f"❌ Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
