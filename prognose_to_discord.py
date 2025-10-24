import json
import os
import requests
from datetime import datetime

WEBHOOK_URL = os.environ.get("PROGNOSE_WEBHOOK")

def build_message():
    with open("results.json", "r") as f:
        results = json.load(f)

    # Auf- und Abwärtstrends sortieren
    up = sorted([r for r in results if r['confidence'] >= 0.85], key=lambda x: x['confidence'], reverse=True)[:10]
    down = sorted([r for r in results if r['confidence'] < 0.85], key=lambda x: x['confidence'])[:10]

    description = f"📊 **Top-Picks Chart-Pattern Analyse** ({datetime.utcnow().strftime('%d.%m.%Y %H:%M UTC')})\n\n"

    description += "**Aufwärtstrends:**\n"
    for r in up:
        description += f"{r['name']}: {', '.join(r['patterns'])} | Confidence: {r['confidence']:.2f}\n"

    description += "\n**Abwärtstrends:**\n"
    for r in down:
        description += f"{r['name']}: {', '.join(r['patterns'])} | Confidence: {r['confidence']:.2f}\n"

    return description

def post_to_discord():
    message = build_message()
    data = {"content": message}

    try:
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Erfolgreich gesendet ✅")
        else:
            print(f"Fehler beim Senden: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception beim Senden: {e}")

if __name__ == "__main__":
    post_to_discord()
