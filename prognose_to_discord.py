from analyzer import run_analysis_patterns
import os
import requests
from datetime import datetime

WEBHOOK_URL = os.environ.get("PROGNOSE_WEBHOOK")

def format_message():
    top_up, top_down = run_analysis_patterns()
    now = datetime.utcnow().strftime("%d.%m.%Y %H:%M Uhr UTC")
    message = f"📊 Top-Picks Chart-Pattern Analyse (höchste Wahrscheinlichkeit) ({now})\n\n"

    message += "Aufwärtspatterns:\n"
    for r in top_up:
        message += f"{r['symbol']}: {', '.join(r['patterns'])} | {r['confidence']:.2f}\n"

    message += "\nAbwärtspatterns:\n"
    for r in top_down:
        message += f"{r['symbol']}: {', '.join(r['patterns'])} | {r['confidence']:.2f}\n"

    return message

def post_to_discord():
    message = format_message()
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": message})
        print("📤 Top-Picks Chart-Pattern Prognose an Discord gesendet!")
    else:
        print("❌ Webhook nicht gefunden!")

if __name__ == "__main__":
    post_to_discord()
