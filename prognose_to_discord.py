import requests
from analyzer import run_analysis
import os

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")
if not WEBHOOK_URL:
    raise ValueError("❌ PROGNOSE_WEBHOOK Secret nicht gefunden. Bitte in GitHub Secrets setzen.")

def post_to_discord():
    message = run_analysis()
    payload = {"content": message}
    r = requests.post(WEBHOOK_URL, json=payload)
    if r.status_code not in [200, 204]:
        print(f"❌ Fehler beim Senden: {r.status_code} - {r.text}")
    else:
        print("✅ Prognose erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    print("📤 Sende Marktprognose an Discord...")
    post_to_discord()
