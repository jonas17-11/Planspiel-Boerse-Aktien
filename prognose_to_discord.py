import os
import io
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import requests
from analyzer import analyze_and_predict_all

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")  # Discord Webhook

def plot_asset(df, name, trend_up=True):
    """Erstellt Diagramm mit Kursen und Prognose."""
    plt.figure(figsize=(8, 4))
    plt.plot(df.index, df['Close'], label='Aktueller Kurs', color='blue')
    
    # Einfache lineare Prognose der letzten 5 Tage
    forecast_days = min(5, len(df))
    y = df['Close'].values[-forecast_days:]
    x = np.arange(forecast_days)
    if len(x) > 1:
        coeffs = np.polyfit(x, y, 1)
        forecast = np.polyval(coeffs, x)
        plt.plot(df.index[-forecast_days:], forecast, linestyle='--',
                 color='green' if trend_up else 'red', label='Prognose')
    
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
    """Erstellt Discord Nachricht und Liste der Assets für Diagramme."""
    message = ""
    assets_to_plot = []

    if top_up:
        message += "**📈 Top steigende Assets:**\n"
        for a in top_up[:5]:
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"
            assets_to_plot.append(a)
        message += "\n"

    if top_down:
        message += "**📉 Top fallende Assets:**\n"
        for a in top_down[:5]:
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"
            assets_to_plot.append(a)

    return message, assets_to_plot

def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    if not top_up and not top_down:
        print("Keine Analyseergebnisse.")
        return

    message, assets_to_plot = build_discord_message(top_up, top_down)

    files = []
    for a in assets_to_plot:
        buf = plot_asset(a['df'], a['name'], trend_up=(a['trend'] == 'up'))
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    if response.status_code in (200, 204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
