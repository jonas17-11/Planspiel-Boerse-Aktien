import os
import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from analyzer import analyze_and_predict_all

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")  # Discord Webhook
TOP_N = 5  # Anzahl der Top Assets

# --- Discord-freundliches Plotten ---
def plot_asset(df, name, trend_up=True):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8,4))

    # Kurslinie
    ax.plot(df.index, df['Close'], label='Kurs', color='#1f77b4', linewidth=2)

    # Prognose
    if len(df) >= 3:
        last_dates = np.arange(len(df))[-3:]
        last_prices = df['Close'].values[-3:]
        coeffs = np.polyfit(last_dates, last_prices, 1)
        next_dates = np.arange(len(df), len(df)+3)
        forecast_prices = np.polyval(coeffs, next_dates)
        forecast_index = pd.date_range(df.index[-1]+pd.Timedelta(days=1), periods=3)
        ax.plot(forecast_index, forecast_prices, '--', color='#2ca02c' if trend_up else '#d62728', linewidth=2, label='Prognose')

    # Achsen + Titel
    ax.set_title(f"{name} - Prognose", fontsize=14, color='white')
    ax.set_xlabel("Datum", fontsize=12, color='white')
    ax.set_ylabel("Preis", fontsize=12, color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.grid(color='gray', linestyle='--', alpha=0.3)
    ax.legend(facecolor='black')

    plt.tight_layout()

    # In Bytes speichern
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor())
    plt.close()
    buf.seek(0)
    return buf

# --- Discord-Nachricht ---
def build_discord_message(top_up, top_down):
    message = ""
    if top_up:
        message += "**📈 Top Assets Steigend:**\n"
        for a in top_up[:TOP_N]:
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    if top_down:
        message += "\n**📉 Top Assets Fallend:**\n"
        for a in top_down[:TOP_N]:
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    return message

# --- Hauptfunktion ---
def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    if not top_up and not top_down:
        print("Keine eindeutigen Patterns gefunden.")
        return

    message = build_discord_message(top_up, top_down)
    files = []

    for a in top_up[:TOP_N] + top_down[:TOP_N]:
        buf = plot_asset(a['df'], a['name'], trend_up=(a['trend']=='up'))
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    response = requests.post(WEBHOOK_URL, data={"content": message}, files=files)
    if response.status_code in (200, 204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
