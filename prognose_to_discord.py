import requests
import time
from analyzer import run_analysis
import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL") or "DEIN_DISCORD_WEBHOOK_HIER"

def post_to_discord():
    message = run_analysis()
    payload = {"content": message}
    r = requests.post(WEBHOOK_URL, json=payload)
    if r.status_code not in [200, 204]:
        print(f"❌ Fehler beim Senden: {r.status_code} - {r.text}")
    else:
        print("✅ Prognose erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    while True:
        print("📤 Sende Marktprognose an Discord...")
        post_to_discord()
        print("🕒 Warte 1 Stunde...\n")
        time.sleep(3600)
