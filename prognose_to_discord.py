import os
import requests
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all  # passt zu deinem analyzer.py
from datetime import datetime

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")
IMAGE_DIR = "charts"  # Ordner für Diagramme
os.makedirs(IMAGE_DIR, exist_ok=True)

def save_chart(asset):
    df = asset["df"]
    forecast = asset["forecast"]

    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["Close"], label="Kurs", color="blue")
    plt.plot(forecast.index, forecast["Predicted"], label="Prognose", color="red", linestyle="--")
    plt.title(f"{asset['name']} - {asset['pattern']}")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
    plt.grid(True, alpha=0.3)

    filename = f"{IMAGE_DIR}/{asset['ticker']}.png"
    plt.savefig(filename, bbox_inches="tight")
    plt.close()
    return filename

def build_discord_message(analysis):
    top_up = sorted(analysis, key=lambda x: x["change"], reverse=True)[:10]
    top_down = sorted(analysis, key=lambda x: x["change"])[:10]

    message = "**📈 Top 10 steigende Assets:**\n"
    for item in top_up:
        message += f"- **{item['name']}**: {item['pattern']} ({item['change']:.2f}%), Aktuell: {item['current']}\n"

    message += "\n**📉 Top 10 sinkende Assets:**\n"
    for item in top_down:
        message += f"- **{item['name']}**: {item['pattern']} ({item['change']:.2f}%), Aktuell: {item['current']}\n"

    message += f"\n_Stand: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}_"
    return message, top_up + top_down  # Wir geben die Assets zurück, um Diagramme zu generieren

def post_to_discord():
    analysis = analyze_and_predict_all()
    if not analysis:
        print("Keine Analyse-Ergebnisse.")
        return

    message, assets_for_chart = build_discord_message(analysis)
    
    # Sende Nachricht
    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code in (200, 204):
        print("Text erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

    # Diagramme senden
    for asset in assets_for_chart:
        chart_file = save_chart(asset)
        with open(chart_file, "rb") as f:
            response = requests.post(
                WEBHOOK_URL,
                files={"file": f},
                data={"content": f"📊 **{asset['name']} - {asset['pattern']}**"}
            )
            if response.status_code in (200, 204):
                print(f"Diagramm für {asset['name']} gesendet ✅")
            else:
                print(f"Fehler beim Senden des Diagramms: {response.status_code}")

if __name__ == "__main__":
    post_to_discord()
