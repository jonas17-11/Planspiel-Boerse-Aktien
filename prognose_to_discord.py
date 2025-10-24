import requests
from analyzer import run_analysis_patterns
import os

# Webhook aus GitHub Secrets
WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")
if not WEBHOOK_URL:
    raise ValueError("❌ PROGNOSE_WEBHOOK Secret nicht gefunden. Bitte in GitHub Secrets setzen.")

def post_to_discord():
    # Analyse starten
    message = run_analysis_patterns()
    
    # Discord limitiert Nachrichten auf 2000 Zeichen → splitten
    chunk_size = 1900
    payloads = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]

    for idx, chunk in enumerate(payloads, start=1):
        r = requests.post(WEBHOOK_URL, json={"content": chunk})
        if r.status_code not in [200, 204]:
            print(f"❌ Fehler beim Senden von Chunk {idx}: {r.status_code} - {r.text}")
        else:
            print(f"✅ Chunk {idx} erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    print("📤 Sende Top-Picks Chart-Pattern Prognose an Discord...")
    post_to_discord()
