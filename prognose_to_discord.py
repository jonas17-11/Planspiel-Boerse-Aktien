import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_all_assets(assets, forecast_days=5):
    """Alle Assets in einem Bild untereinander plotten mit Richtungspfeilen"""
    n = len(assets)
    fig, axes = plt.subplots(n, 1, figsize=(8, 4*n), sharex=False)
    
    if n == 1:
        axes = [axes]  # Damit es immer iterierbar ist

    for ax, a in zip(axes, assets):
        df = a['df']
        name = a['name']
        trend_up = (a['trend'] == "up")
        symbol = "📈" if trend_up else "📉"
        
        ax.plot(df.index, df['Close'], label='Kurs', color='blue')
        
        # Lineare Prognose
        y = df['Close'].values
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, 1)
        forecast_x = np.arange(len(y), len(y)+forecast_days)
        forecast_y = np.polyval(coeffs, forecast_x)
        # Prognose auf letzten Kurs verschieben
        shift = y[-1] - forecast_y[0]
        forecast_y += shift
        forecast_dates = pd.date_range(start=df.index[-1], periods=forecast_days+1, freq='D')[1:]
        ax.plot(forecast_dates, forecast_y, linestyle='--', color='green' if trend_up else 'red',
                label='Prognose', marker='o', markersize=4)
        
        # Richtungssymbol oberhalb der Prognose
        ax.text(forecast_dates[-1], forecast_y[-1]*1.01, symbol, fontsize=16, ha='center')

        ax.set_title(f"{name} - {a['pattern']} ({a['confidence']}%)")
        ax.set_ylabel("Preis")
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend()
    
    plt.xlabel("Datum")
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
    all_assets = top_up + top_down
    if not all_assets:
        print("Keine relevanten Muster gefunden.")
        return

    message = build_discord_message(top_up, top_down)

    # Alle Diagramme in einem Bild
    buf = plot_all_assets(all_assets)
    files = [("file", ("prognosen.png", buf, "image/png"))]

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    
    if response.status_code in (200,204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
