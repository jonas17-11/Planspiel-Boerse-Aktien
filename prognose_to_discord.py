import os
import json
import pandas as pd
import requests

# Discord Webhook aus GitHub Secrets
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# Farben für Embed
COLOR_UPTREND = 0x00FF00   # Grün
COLOR_DOWNTREND = 0xFF0000 # Rot
COLOR_NEUTRAL = 0xFFFF00   # Gelb

# Analyseergebnisse laden
CSV_FILE = "analysis_results.csv"
df = pd.read_csv(CSV_FILE)

# Top 5 Assets nach Confidence auswählen
df_sorted = df.sort_values(by="confidence", ascending=False)
top_assets = df_sorted.head(5)

def create_embed(asset):
    trend_color = COLOR_UPTREND if asset["trend"]=="Uptrend" else COLOR_DOWNTREND
    pattern = asset["pattern"] if pd.notna(asset["pattern"]) else "–"
    confidence = f"{asset['confidence']*100:.1f}%"
    
    embed = {
        "title": f"{asset['name']} ({asset['ticker']})",
        "color": trend_color,
        "fields": [
            {"name": "Trend", "value": asset["trend"], "inline": True},
            {"name": "Pattern", "value": pattern, "inline": True},
            {"name": "Confidence", "value": confidence, "inline": True},
        ],
        "image": {"url": f"attachment://{os.path.basename(asset['chart'])}"}
    }
    return embed

def send_to_discord(assets):
    files = []
    embeds = []
    for asset in assets.to_dict(orient="records"):
        chart_path = asset["chart"]
        if os.path.exists(chart_path):
            files.append(("file", (os.path.basename(chart_path), open(chart_path, "rb"), "image/png")))
        embeds.append(create_embed(asset))
    
    payload = {
        "username": "📈 Markt-Analyzer",
        "embeds": embeds
    }
    
    response = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files)
    if response.status_code == 204 or response.status_code == 200:
        print("Analyse erfolgreich an Discord gesendet!")
    else:
        print(f"Fehler beim Senden: {response.status_code}, {response.text}")

if __name__ == "__main__":
    send_to_discord(top_assets)
