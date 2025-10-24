import os
import requests
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def build_discord_message(analysis):
    # Top 10 Aufwärts
    top_up = sorted([a for a in analysis if a['pattern'].startswith("Aufwärts")],
                    key=lambda x: x['confidence'], reverse=True)[:10]
    # Top 10 Abwärts
    top_down = sorted([a for a in analysis if a['pattern'].startswith("Abwärts")],
                      key=lambda x: x['confidence'], reverse=True)[:10]

    message = "**📊 Top 10 Aufwärts-Trends:**\n"
    for item in top_up:
        message += f"- **{item['name']}**: {item['pattern']} ({item['confidence']}%)\n"

    message += "\n**📉 Top 10 Abwärts-Trends:**\n"
    for item in top_down:
        message += f"- **{item['name']}**: {item['pattern']} ({item['confidence']}%)\n"

    return message

def post_to_discord():
    analysis = get_analysis()
    if not analysis:
        print("Keine Analyse-Ergebnisse.")
        return

    message = build_discord_message(analysis)
    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
