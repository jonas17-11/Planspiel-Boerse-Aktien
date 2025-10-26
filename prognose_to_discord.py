import os
import requests
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def post_to_discord():
    top, flop = get_analysis()
    if not top and not flop:
        print("Keine Analyse-Ergebnisse.")
        return

    message = "**📊 Top 10 steigende Assets:**\n"
    for a in top:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    message += "\n**📉 Top 10 sinkende Assets:**\n"
    for a in flop:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

    # Charts hochladen
    for asset in top+flop:
        if asset["chart"]:
            with open(asset["chart"], "rb") as f:
                files = {"file": f}
                response = requests.post(WEBHOOK_URL, files=files)
                if response.status_code != 204:
                    print(f"Fehler beim Hochladen von {asset['name']}: {response.status_code}")

if __name__ == "__main__":
    post_to_discord()
