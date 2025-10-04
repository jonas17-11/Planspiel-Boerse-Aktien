import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import requests
from discord import SyncWebhook
from datetime import datetime
import io

# 📌 Hole Secrets
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 📈 Lade Aktien-Daten (z.B. aus monitor_output.json)
with open("monitor_output.json", "r", encoding="utf-8") as f:
    stock_data = json.load(f)

df = pd.DataFrame(stock_data)
df["change_percent"] = ((df["price"] - df["previous_close"]) / df["previous_close"]) * 100

# Sortiere für Top & Flop
top_stocks = df.sort_values("change_percent", ascending=False).head(5)
worst_stocks = df.sort_values("change_percent", ascending=True).head(5)

# 📊 Diagramm erzeugen (Top 5)
plt.figure(figsize=(10, 5))
plt.bar(top_stocks["ticker"], top_stocks["change_percent"], color="green")
plt.title("Top 5 Aktien - Veränderung (%)")
plt.xlabel("Ticker")
plt.ylabel("% Veränderung")
plt.tight_layout()

# In Speicher speichern
buf = io.BytesIO()
plt.savefig(buf, format="png")
buf.seek(0)
plt.close()

# Diagramm-Datei erstellen
chart_file_path = "top_stocks_chart.png"
with open(chart_file_path, "wb") as img_file:
    img_file.write(buf.getbuffer())

# 📄 Tabelle in Textform
table_text = df.to_string(index=False, formatters={"change_percent": "{:.2f}%".format})

# 🧠 Anfrage an OpenRouter (Mistral 7B Instruct)
prompt_text = f"""
Analysiere folgende Aktienkursveränderungen und gib eine kurze Einschätzung,
welche Aktien derzeit interessant für Investitionen sein könnten (hypothetisch, keine Finanzberatung).

Daten:
{table_text}

Gib am Ende eine klare Empfehlungsliste mit Top Chancen und Risiken.
"""

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com",  # optional
    "X-Title": "Stock Analysis Bot"
}

payload = {
    "model": "mistralai/mistral-7b-instruct",
    "messages": [
        {"role": "system", "content": "Du bist ein Finanzanalyse-Assistent. Gib klare, strukturierte Einschätzungen ab."},
        {"role": "user", "content": prompt_text}
    ],
    "temperature": 0.7
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload
)

if response.status_code != 200:
    ai_text = f"❌ KI konnte keine Antwort generieren. ({response.status_code})\n{response.text}"
else:
    ai_text = response.json()["choices"][0]["message"]["content"]

# 📬 An Discord schicken
webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)

# Tabelle und KI Fazit
webhook.send(f"📊 **Aktienübersicht - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**\n```\n{table_text}\n```\n🤖 **KI Fazit:**\n{ai_text}")

# Bild separat anhängen
with open(chart_file_path, "rb") as f:
    webhook.send(file=f)
