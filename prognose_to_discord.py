import os
import io
import base64
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")  # Discord Webhook

def plot_asset(df, forecast_df, name, trend_up=True):
    plt.figure(figsize=(8, 4))
    plt.plot(df.index, df['Close'], label='Aktueller Kurs', color='blue')
    plt.plot(forecast_df.index, forecast_df['Predicted'], label='Prognose', color='green' if trend_up else 'red', linestyle='--')
    plt.title(f"{name} - Prognose")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
    plt.tight_layout()

    # In Bytes speichern
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def build_discord_message(analysis):
    # Sortieren nach Wahrscheinlichkeit/Confidence
    rising = sorted([a for a in analysis if a['trend'] == 'up'], key=lambda x: x['confidence'], reverse=True)[:10]
    falling = sorted([a for a in analysis if a['trend'] == 'down'], key=lambda x: x['confidence'], reverse=True)[:10]

    message = "**📈 Top 10 Steigende Assets:**\n"
    for a in rising:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    message += "\n**📉 Top 10 Fallende Assets:**\n"
    for a in falling:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    return message, rising + falling

def post_to_discord():
    analysis = analyze_and_predict_all()
    if not analysis:
        print("Keine Analyseergebnisse.")
        return

    message, assets_to_plot = build_discord_message(analysis)

    # Bilder hochladen
    files = []
    for a in assets_to_plot:
        buf = plot_asset(a['df'], a['forecast_df'], a['name'], trend_up=(a['trend'] == 'up'))
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    # Nachricht senden
    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    if response.status_code in (200, 204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
