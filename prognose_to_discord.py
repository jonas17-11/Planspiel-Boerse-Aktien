import os
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_all_assets(top_up, top_down, forecast_days=5):
    plt.figure(figsize=(12,6))

    plotted_labels = set()

    ax = plt.gca()

    # --- Hintergrund einfärben ---
    if top_up:
        ax.axhspan(0, 1, facecolor='green', alpha=0.05, zorder=0)
    if top_down:
        ax.axhspan(0, 1, facecolor='red', alpha=0.05, zorder=0)

    # --- Alle steigenden Assets ---
    for a in top_up:
        df = a['df']
        label_course = f"{a['name']} Kurs"
        if label_course not in plotted_labels:
            ax.plot(df.index, df['Close'], label=label_course, linewidth=1.5)
            plotted_labels.add(label_course)
        else:
            ax.plot(df.index, df['Close'], linewidth=1.5, color='blue')

        # lineare Prognose
        y = df['Close'].values
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, 1)
        forecast_x = np.arange(len(y), len(y)+forecast_days)
        forecast_y = np.polyval(coeffs, forecast_x)
        shift = y[-1] - forecast_y[0]
        forecast_y += shift
        forecast_dates = pd.date_range(start=df.index[-1], periods=forecast_days+1, freq='D')[1:]

        label_forecast = f"{a['name']} Prognose ↑"
        if label_forecast not in plotted_labels:
            ax.plot(forecast_dates, forecast_y, linestyle='--', color='green', linewidth=2, marker='o', markersize=5, label=label_forecast)
            plotted_labels.add(label_forecast)
        else:
            ax.plot(forecast_dates, forecast_y, linestyle='--', color='green', linewidth=2, marker='o', markersize=5)

    # --- Alle fallenden Assets ---
    for a in top_down:
        df = a['df']
        label_course = f"{a['name']} Kurs"
        if label_course not in plotted_labels:
            ax.plot(df.index, df['Close'], label=label_course, linewidth=1.5)
            plotted_labels.add(label_course)
        else:
            ax.plot(df.index, df['Close'], linewidth=1.5, color='blue')

        # lineare Prognose
        y = df['Close'].values
        x = np.arange(len(y))
        coeffs = np.polyfit(x, y, 1)
        forecast_x = np.arange(len(y), len(y)+forecast_days)
        forecast_y = np.polyval(coeffs, forecast_x)
        shift = y[-1] - forecast_y[0]
        forecast_y += shift
        forecast_dates = pd.date_range(start=df.index[-1], periods=forecast_days+1, freq='D')[1:]

        label_forecast = f"{a['name']} Prognose ↓"
        if label_forecast not in plotted_labels:
            ax.plot(forecast_dates, forecast_y, linestyle='--', color='red', linewidth=2, marker='o', markersize=5, label=label_forecast)
            plotted_labels.add(label_forecast)
        else:
            ax.plot(forecast_dates, forecast_y, linestyle='--', color='red', linewidth=2, marker='o', markersize=5)

    ax.set_title("Top Assets - Prognosen", fontsize=14)
    ax.set_xlabel("Datum")
    ax.set_ylabel("Preis")
    ax.grid(True, linestyle=':', alpha=0.5)

    # --- Übersichtliche Legende ---
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), fontsize=8, loc='upper left', bbox_to_anchor=(1,1))

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
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
    buf = plot_all_assets(top_up, top_down)

    payload = {"content": message}
    files = [("file", ("top_assets.png", buf, "image/png"))]
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    
    if response.status_code in (200,204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
