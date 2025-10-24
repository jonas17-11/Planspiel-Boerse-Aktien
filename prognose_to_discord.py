import os
import requests
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def build_discord_message(analysis):
    if not analysis:
        return "Keine Analyse-Ergebnisse.", []

    # Sortieren nach Confidence
    sorted_up = sorted([a for a in analysis if a["pattern"].startswith("Aufwärts")], key=lambda x: x["confidence"], reverse=True)[:10]
    sorted_down = sorted([a for a in analysis if a["pattern"].startswith("Abwärts")], key=lambda x: x["confidence"], reverse=True)[:10]

    message = "**📈 Top 10 Aufwärts-Trends:**\n"
    for item in sorted_up:
        message += f"- **{item['name']}**: {item['pattern']} ({item['confidence']}%)\n"

    message += "\n**📉 Top 10 Abwärts-Trends:**\n"
    for item in sorted_down:
        message += f"- **{item['name']}**: {item['pattern']} ({item['confidence']}%)\n"

    # Alle Chart-Dateien sammeln
    chart_files = [a["chart"] for a in analysis if a.get("chart")]

    return message, chart_files

def post_to_discord():
    analysis = get_analysis()
    if not analysis:
        print("Keine Analyse-Ergebnisse.")
        return

    message, chart_files = build_discord_message(analysis)

    # Multipart-Form erstellen, um Text + Bilder in einem Post zu senden
    multipart_data = [("content", message)]
    for i, chart_path in enumerate(chart_files):
        if os.path.exists(chart_path):
            multipart_data.append(("files[]", (os.path.basename(chart_path), open(chart_path, "rb"))))

    response = requests.post(WEBHOOK_URL, files=multipart_data)
    if response.status_code == 204:
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
