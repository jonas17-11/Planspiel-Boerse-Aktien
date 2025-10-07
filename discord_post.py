import json
import os
import pandas as pd
from discord import SyncWebhook, File

# Secrets aus GitHub Actions
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

# Lade monitor_output.json
with open("monitor_output.json", "r") as f:
    data = json.load(f)

top5 = pd.DataFrame(data["top5"])
bottom5 = pd.DataFrame(data["bottom5"])
ki_text = data.get("ki", "⚠️ Keine KI-Einschätzung verfügbar.")

# Formatiere Tabellen als Markdown
def df_to_md(df):
    return "```\n" + df.to_string(index=False) + "\n```"

top_md = df_to_md(top5)
bottom_md = df_to_md(bottom5)

# Nachricht zusammenstellen
message = (
    f"**📊 Top 5 Aktien**\n{top_md}\n\n"
    f"**📉 Bottom 5 Aktien**\n{bottom_md}\n\n"
    f"**🤖 KI Einschätzung**\n{ki_text}"
)

# Discord Webhook senden
try:
    webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
    # Tabelle + KI Text als Nachricht, Diagramm als Datei anhängen
    if os.path.exists("monitor_plot.png"):
        with open("monitor_plot.png", "rb") as f:
            webhook.send(content=message, file=File(f, filename="monitor_plot.png"))
    else:
        webhook.send(content=message)
    print("✅ Nachricht erfolgreich gesendet.")
except Exception as e:
    print(f"❌ Fehler beim Senden an Discord: {e}")
