import os
import json
import pandas as pd
from discord import SyncWebhook
import matplotlib.pyplot as plt
from openai import OpenAI

# 🔹 Lade Daten
with open("monitor_output.json", "r") as f:
    data = json.load(f)

# Beispiel: erstelle Tabelle der Top 10 und Bottom 5
df = pd.DataFrame(data)
top10 = df.nlargest(10, "change_percent")
bottom5 = df.nsmallest(5, "change_percent")

# 🔹 Diagramm erstellen für Top 5 Aktien
plt.figure(figsize=(10,6))
plt.bar(top10["ticker"], top10["change_percent"], color="green")
plt.title("Top 10 Aktien der Stunde")
plt.ylabel("Veränderung (%)")
plt.savefig("top10_chart.png")
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
message = f"**Top 10 Aktien:**\n{top10.to_string(index=False)}\n\n**Bottom 5 Aktien:**\n{bottom5.to_string(index=False)}"

# 🔹 KI Fazit generieren
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if OPENROUTER_API_KEY:
    client = OpenAI(api_key=OPENROUTER_API_KEY)
    prompt = f"Hier sind die aktuellen Aktienwerte:\n{df.to_string(index=False)}\n\nGib mir eine kurze Analyse und Hypothesen, wo es sinnvoll sein könnte zu investieren."
    try:
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

# 🔹 Nachricht + Chart senden
with open("top10_chart.png", "rb") as f:
    webhook.send(content=message, file=SyncWebhook.file(f))
