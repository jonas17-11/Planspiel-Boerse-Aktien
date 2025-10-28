import os
import io
import pandas as pd
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

# --- Candlestick-Diagramm in Subplots für alle Assets ---
def plot_multiple_assets(assets):
    n = len(assets)
    fig, axes = plt.subplots(n, 1, figsize=(10, 4*n), sharex=False)
    if n == 1:
        axes = [axes]
    for ax, a in zip(axes, assets):
        df = a['df'][-30:].copy()  # letzte 30 Tage
        for idx, row in df.iterrows():
            open_price = float(row['Open'])
            close_price = float(row['Close'])
            high_price = float(row['High'])
            low_price = float(row['Low'])
            color = 'green' if close_price >= open_price else 'red'
            ax.plot([idx, idx], [low_price, high_price], color='black', linewidth=1)
            ax.add_patch(plt.Rectangle((idx - pd.Timedelta(hours=12), min(open_price, close_price)),
                                       pd.Timedelta(hours=24), abs(open_price - close_price),
                                       color=color))
        ax.set_ylabel("Preis")
        ax.set_title(f"{a['name']} - {a['pattern']} ({a['confidence']}%)")
        ax.grid(True)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

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

# --- Posten an Discord ---
def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    all_assets = sorted(top_up + top_down, key=lambda x: x['confidence'], reverse=True)[:10]  # Top 10
    if not all_assets:
        print("Keine relevanten Muster gefunden.")
        return

    message = build_discord_message(top_up, top_down)
    buf = plot_multiple_assets(all_assets)
    files = [("file", ("top_assets.png", buf, "image/png"))]

    response = requests.post(WEBHOOK_URL, data={"content": message}, files=files)
    if response.status_code in (200, 204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
