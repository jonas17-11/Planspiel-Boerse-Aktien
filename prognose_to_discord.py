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
    width = 0.02
    for i, row in enumerate(df_plot.itertuples()):
        open_price = float(row.Open)
        close_price = float(row.Close)
        high_price = float(row.High)
        low_price = float(row.Low)
        color = 'green' if close_price >= open_price else 'red'
        ax.add_patch(Rectangle((i - width/2, min(open_price, close_price)),
                               width, abs(open_price - close_price), color=color))
        ax.vlines(i, low_price, high_price, color=color, linewidth=1)
    
    ax.set_title(name)
    ax.set_ylabel("Preis")
    ax.set_xticks([])

    # --- Dynamischer Prognosepfeil leicht nach rechts versetzt ---
    y_top = df_plot['High'].max()
    y_range = df_plot['High'].max() - df_plot['Low'].min()
    arrow_height = y_range * 0.1 * (confidence / 100)

    base_color = np.array(to_rgba('green' if trend_up else 'red'))
    intensity = 0.4 + 0.6*(confidence/100)
    arrow_color = tuple(base_color[:3]*intensity) + (1.0,)

    ax.annotate('',
                xy=(len(df_plot)-1 + 0.5, y_top + arrow_height),
                xytext=(len(df_plot)-1 + 0.5, y_top),
                arrowprops=dict(facecolor=arrow_color, edgecolor=arrow_color, shrink=0.05, width=3, headwidth=8))

    trend_text = "Aufwärts" if trend_up else "Abwärts"
    ax.text(0.5, -0.15, f"Prognose: {trend_text} {confidence}%", ha='center', va='center', transform=ax.transAxes)

# --- Discord-Nachricht bauen ---
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

# --- Alles analysieren und posten ---
def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    all_assets = top_up + top_down
    if not all_assets:
        print("Keine relevanten Muster gefunden.")
        return

    message = build_discord_message(top_up, top_down)

    # --- Subplots für alle Top-Assets in einem Bild ---
    n = len(all_assets)
    fig, axes = plt.subplots(n, 1, figsize=(10, 3*n), constrained_layout=True)
    if n == 1:
        axes = [axes]

    for ax, a in zip(axes, all_assets):
        plot_candlestick_subplot(ax, a['df'], a['name'], trend_up=(a['trend']=="up"), confidence=a['confidence'])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    payload = {"content": message}
    files = [("file", ("top_assets.png", buf, "image/png"))]

    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    if response.status_code in (200,204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
