import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from discord import SyncWebhook, File
from openai import OpenAI

# 🔹 Daten laden
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# 🔹 Top/Bottom 5 berechnen
top5 = df.nlargest(5, "change_percent")
bottom5 = df.nsmallest(5, "change_percent")

# 🔹 Diagramm Top5 + Bottom5 erstellen
plt.figure(figsize=(12,6))
plt.bar(top5["ticker"], top5["change_percent"], color="green", label="Top 5")
plt.bar(bottom5["ticker"], bottom5["change_percent"], color="red", label="Bottom 5")
plt.title("Top 5 und Bottom 5 Aktien der Stunde")
plt.ylabel("Veränderung (%)")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig("top_bottom_chart.png")
plt.close()

# 🔹 Discord Webhook laden
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
if not DISCORD_WEBHOOK_URL:
    raise ValueError("Kein Discord Webhook Secret gefunden. Bitte DISCORD_WEBHOOK als Secret setzen!")

try:
    webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
except Exception as e:
    raise ValueError(f"Webhook URL ungültig: {e}")

# 🔹 Nachricht zusammenstellen
message = f"**Top 5 Aktien:**\n{top5.to_string(index=False)}\n\n**Bottom 5 Aktien:**\n{bottom5.to_string(index=False)}"

# 🔹 KI Fazit generieren (nur wenn API-Key korrekt)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if OPENROUTER_API_KEY:
    try:
        client = OpenAI(api_key=OPENROUTER_API_KEY)
        prompt = f"Hier sind die aktuellen Aktienwerte:\n{df.to_string(index=False)}\n\nGib mir eine kurze Analyse und Hypothesen, wo es sinnvoll sein könnte zu investieren."
        response = client.chat.completions.create(
            model="mistral-7b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250
        )
        ai_message = response.choices[0].message.content
        message += f"\n\n**KI Fazit:**\n{ai_message}"
    except Exception as e:
        message += f"\n\n⚠️ KI konnte nicht antworten: {e}"

# 🔹 Nachricht + Diagramm senden
with open("top_bottom_chart.png", "rb") as f:
    webhook.send(content=message, file=File(f, filename="top_bottom_chart.png"))
