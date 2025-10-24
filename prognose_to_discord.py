import os
import io
import requests
import matplotlib.pyplot as plt
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_asset(df, ticker_name, pattern):
    plt.figure(figsize=(6,3))
    plt.plot(df.index, df['Close'], label='Close', color='blue')
    plt.title(f"{ticker_name} ({pattern})", fontsize=10)
    plt.xlabel("Datum", fontsize=8)
    plt.ylabel("Preis", fontsize=8)
    plt.xticks(rotation=45, fontsize=6)
    plt.yticks(fontsize=6)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def post_to_discord():
    analysis = get_analysis()
    if not analysis:
        print("Keine Analyse-Ergebnisse.")
        return

    # Sortieren nach Confidence
    top_up = sorted(analysis, key=lambda x: x["confidence"], reverse=True)[:10]
    top_down = sorted(analysis, key=lambda x: x["confidence"])[:10]

    # Discord Embed Nachricht vorbereiten
    embeds = []

    for section_name, section in [("📈 Top 10 Aufsteiger", top_up), ("📉 Top 10 Absteiger", top_down)]:
        for asset in section:
            buf = plot_asset(asset['df'], asset['name'], asset['pattern'])
            
            # Discord erlaubt keine direkten Bild-Uploads in Content via Webhook; wir laden als multipart
            files = {"file": (f"{asset['ticker']}.png", buf)}
            payload = {
                "content": f"**{section_name}**\n**{asset['name']}**: {asset['pattern']} ({asset['confidence']}%)"
            }
            response = requests.post(WEBHOOK_URL, data=payload, files=files)
            if response.status_code == 204 or response.status_code == 200:
                print(f"{asset['name']} erfolgreich gesendet ✅")
            else:
                print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
