import os
import io
import matplotlib.pyplot as plt
import requests
from analyzer import analyze_and_predict_all

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")  # Discord Webhook

def plot_asset(df, forecast_df, name, trend_up=True):
    plt.figure(figsize=(8, 4))
    plt.plot(df.index, df['Close'], label='Aktueller Kurs', color='blue')
    plt.plot(forecast_df.index, forecast_df['Predicted'], 
             label='Prognose', color='green' if trend_up else 'red', linestyle='--')
    plt.title(f"{name} - Prognose")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

def build_discord_messages(top_up, top_down):
    messages = []

    # Top Up
    for a in top_up:
        msg = f"📈 **{a['name']}**\nPattern: {a['pattern']}\nTrend: {a['trend']}\nConfidence: {a['confidence']}%"
        messages.append((msg, a))

    # Top Down
    for a in top_down:
        msg = f"📉 **{a['name']}**\nPattern: {a['pattern']}\nTrend: {a['trend']}\nConfidence: {a['confidence']}%"
        messages.append((msg, a))

    return messages

def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    if not top_up and not top_down:
        print("Keine Analyseergebnisse.")
        return

    messages = build_discord_messages(top_up, top_down)

    for msg, asset in messages:
        files = []
        buf = plot_asset(asset['df'], asset['forecast_df'], asset['name'], trend_up=(asset['trend']=='up'))
        files.append(("file", (f"{asset['ticker']}.png", buf, "image/png")))

        payload = {"content": msg}
        response = requests.post(WEBHOOK_URL, data=payload, files=files)
        if response.status_code in (200, 204):
            print(f"Erfolgreich gesendet: {asset['name']}")
        else:
            print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
