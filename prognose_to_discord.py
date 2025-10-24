import os
import io
import requests
import matplotlib.pyplot as plt
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_chart(df, forecast, name):
    plt.figure(figsize=(8, 4))
    plt.plot(df.index, df['Close'], label='Historisch', color='blue')
    plt.plot(forecast.index, forecast['Predicted'], label='Prognose', color='red', linestyle='--')
    plt.title(f"{name} Kurs & Prognose")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
    plt.tight_layout()
    
    # In Bytes speichern für Discord Upload
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def build_discord_message(analysis):
    # Sortiere nach predicted_change
    sorted_analysis = sorted(analysis, key=lambda x: x['predicted_change'], reverse=True)
    top_up = sorted_analysis[:10]
    top_down = sorted_analysis[-10:]

    message = "**📊 Top 10 Steigende Assets:**\n"
    for item in top_up:
        message += f"- **{item['name']}**: {item['pattern']} ({item['predicted_change']:.2f}%)\n"

    message += "\n**📉 Top 10 Fallende Assets:**\n"
    for item in reversed(top_down):  # Absteigend sortieren
        message += f"- **{item['name']}**: {item['pattern']} ({item['predicted_change']:.2f}%)\n"

    return message, top_up + top_down

def post_to_discord():
    analysis = get_analysis()
    if not analysis:
        print("Keine Analyse-Ergebnisse.")
        return

    message, chart_assets = build_discord_message(analysis)

    # Discord Webhook: Text senden
    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Text erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

    # Charts als Bild hochladen (Top 5 steigende + fallende)
    for item in chart_assets[:5]:
        buf = plot_chart(item['df'], item['forecast'], item['name'])
        files = {'file': (f"{item['ticker']}.png", buf, 'image/png')}
        response = requests.post(WEBHOOK_URL, files=files)
        if response.status_code == 204:
            print(f"Chart {item['name']} erfolgreich gesendet ✅")
        else:
            print(f"Fehler beim Senden Chart {item['name']}: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
