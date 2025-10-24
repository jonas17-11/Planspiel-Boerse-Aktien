import os
import requests
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def build_discord_message(analysis):
    if not analysis:
        return "Keine Analyse-Ergebnisse verfügbar."

    # Sortiere nach Aufwärtstrend (höchster positiver Change)
    top_up = sorted([a for a in analysis if a["confidence"] > 0], key=lambda x: x["confidence"], reverse=True)[:10]

    # Sortiere nach Abwärtstrend (höchster negativer Change)
    top_down = sorted([a for a in analysis if a["confidence"] < 0], key=lambda x: x["confidence"])[:10]

    message = "**📊 Top 10 Aufwärts-Trends:**\n"
    if top_up:
        for item in top_up:
            message += f"- **{item['name']}**: {item['pattern']} ({item['confidence']}%)\n"
    else:
        message += "Keine Aufwärtstrends in den letzten Tagen 📉\n"

    message += "\n**📉 Top 10 Abwärts-Trends:**\n"
    if top_down:
        for item in top_down:
            message += f"- **{item['name']}**: {item['pattern']} ({item['confidence']}%)\n"
    else:
        message += "Keine Abwärtstrends in den letzten Tagen 📈\n"

    return message

def post_to_discord():
    analysis = get_analysis()
    message = build_discord_message(analysis)

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
