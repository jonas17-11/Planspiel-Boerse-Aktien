# prognose_to_discord.py
import os
import io
import matplotlib.pyplot as plt
from analyzer import get_analysis
import requests

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

def plot_asset(asset):
    df = asset["df"]
    forecast = asset.get("forecast")
    plt.figure(figsize=(10, 4))
    plt.plot(df.index, df["Close"], label="Aktueller Kurs", color="blue", linewidth=2)
    if forecast is not None:
        plt.plot(forecast.index, forecast["Predicted"], 
                 label="Prognose", 
                 color="green" if asset["trend"] > 0 else "red",
                 linestyle="--", linewidth=2)
    plt.title(f"{asset['name']} ({asset['pattern']})")
    plt.xlabel("Datum")
    plt.ylabel("Kurs")
    plt.legend()
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf

def build_discord_message(analysis):
    # Top 10 steigende & Top 10 fallende
    rising = sorted([a for a in analysis if a["trend"] > 0], key=lambda x: x["confidence"], reverse=True)[:10]
    falling = sorted([a for a in analysis if a["trend"] < 0], key=lambda x: x["confidence"], reverse=True)[:10]

    message = "**📈 Top 10 Steigende Assets:**\n"
    for a in rising:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    message += "\n**📉 Top 10 Fallende Assets:**\n"
    for a in falling:
        message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n"

    return message, rising + falling

def post_to_discord():
    analysis = get_analysis()
    if not analysis:
        print("Keine Analyse-Ergebnisse.")
        return

    message, assets_to_plot = build_discord_message(analysis)

    # Text senden
    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Text erfolgreich gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

    # Bilder senden
    for asset in assets_to_plot:
        img_buf = plot_asset(asset)
        files = {"file": ("plot.png", img_buf)}
        response = requests.post(WEBHOOK_URL, files=files)
        if response.status_code == 204:
            print(f"{asset['name']} Diagramm erfolgreich gesendet ✅")
        else:
            print(f"Fehler beim Senden von {asset['name']}: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
