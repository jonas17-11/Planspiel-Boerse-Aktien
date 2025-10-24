import os
import requests
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def build_discord_message(analysis):
    # Sortiere nach Confidence und nehme Top 10
    sorted_results = sorted(analysis, key=lambda x: x["confidence"], reverse=True)[:10]

    message = "**📊 Top 10 Chart-Patterns:**\n"
    for item in sorted_results:
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
