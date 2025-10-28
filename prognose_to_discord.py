import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_asset(df, name, trend_up=True, forecast_days=5):
    plt.figure(figsize=(8,4))
    plt.plot(df.index, df['Close'], label='Kurs', color='blue')

    # --- Einfache lineare Prognose ---
    last_index = df.index[-1]
    y = df['Close'].values
    x = np.arange(len(y))
    coeffs = np.polyfit(x, y, 1)
    forecast_x = np.arange(len(y), len(y)+forecast_days)
    forecast_y = np.polyval(coeffs, forecast_x)
    forecast_dates = pd.date_range(start=last_index, periods=forecast_days+1, freq='D')[1:]
    plt.plot(forecast_dates, forecast_y, label='Prognose', linestyle='--', color='green' if trend_up else 'red')

    plt.title(f"{name} - Prognose")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
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
    if not top_up and not top_down:
        print("Keine relevanten Muster gefunden.")
        return

    message = build_discord_message(top_up, top_down)

    files = []
    for a in top_up + top_down:
        buf = plot_asset(a['df'], a['name'], trend_up=(a['trend']=="up"))
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    payload = {"content": message}
    try:
        response = requests.post(WEBHOOK_URL, data=payload, files=files)
        if response.status_code in (200, 204):
            print("Erfolgreich in Discord gesendet ✅")
        else:
            print(f"Fehler beim Senden: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Fehler beim Senden an Discord: {e}")

if __name__ == "__main__":
    post_to_discord()
