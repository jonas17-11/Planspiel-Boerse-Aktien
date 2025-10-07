import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from discord import SyncWebhook, File
import google.generativeai as genai

# 🔸 Gemini konfigurieren
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ Kein GEMINI_API_KEY gefunden — KI Fazit wird übersprungen.")

# 🔸 Aktien-Daten laden
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# 🔸 Top 5 und Bottom 5 berechnen
top5 = df.nlargest(5, "change_percent")
bottom5 = df.nsmallest(5, "change_percent")

# 🔸 Diagramm erstellen (Top 5 = grün, Bottom 5 = rot)
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

# 🔸 Discord Webhook
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
if not DISCORD_WEBHOOK_URL:
    raise ValueError("❌ Kein Discord Webhook Secret gefunden!")

webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)

# 🔸 Basisnachricht mit Tabellen
message = f"📊 **Top 5 Aktien:**\n```\n{top5.to_string(index=False)}\n```\n"
message += f"📉 **Bottom 5 Aktien:**\n```\n{bottom5.to_string(index=False)}\n```"

# 🔸 KI Fazit mit Gemini generieren
if GEMINI_API_KEY:
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = (
            "Hier ist eine Tabelle mit Aktienwerten (Ticker, Preis, Veränderung):\n\n"
            f"{df.to_string(index=False)}\n\n"
            "Gib mir bitte eine kurze Analyse mit möglichen Investment-Hypothesen und Empfehlungen."
        )
        response = model.generate_content(prompt)
        if response.text:
            message += f"\n🤖 **Gemini Fazit:**\n{response.text}"
        else:
            message += "\n⚠️ KI hat keine Antwort zurückgegeben."
    except Exception as e:
        message += f"\n⚠️ KI-Fehler: {e}"

# 🔸 Nachricht mit Bild senden
with open("top_bottom_chart.png", "rb") as f:
    webhook.send(content=message, file=File(f, filename="top_bottom_chart.png"))
