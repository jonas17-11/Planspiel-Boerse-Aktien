import os
import io
import matplotlib.pyplot as plt
from analyzer import analyze_and_predict_all
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")  # Discord Webhook

def plot_asset(df, name, trend_up=True):
    plt.figure(figsize=(8,4))
    plt.plot(df.index, df['Close'], label='Kurs', color='blue')
    plt.title(f"{name} - Prognose")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.grid(True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def build_discord_message(top_up, top_down):
    message = "**📈 Top 5 Steigende Assets:**\n"
    for a in top_up:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    message += "\n**📉 Top 5 Fallende Assets:**\n"
    for a in top_down:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    return message, top_up + top_down

def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    if not top_up and not top_down:
        print("Keine Analyseergebnisse.")
        return

    message, assets_to_plot = build_discord_message(top_up, top_down)

    files = []
    for a in assets_to_plot:
        buf = plot_asset(a['df'], a['name'], trend_up=(a['trend']=='up'))
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    if response.status_code in (200, 204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
