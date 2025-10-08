import os
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
from discord import SyncWebhook, File

# === 🔐 Secrets laden ===
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# === 📊 Daten laden ===
df = pd.read_json("monitor_output.json")

# Top 5 & Bottom 5 Aktien bestimmen
top5 = df.nlargest(5, 'change_percent')
bottom5 = df.nsmallest(5, 'change_percent')

# === 🧾 Tabellen für Discord formatieren ===
def df_to_discord_table(dataframe):
    header = "| " + " | ".join(dataframe.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(dataframe.columns)) + " |"
    rows = "\n".join(
        "| " + " | ".join(str(x) for x in row) + " |"
        for row in dataframe.values
    )
    return f"{header}\n{separator}\n{rows}"

top_table = df_to_discord_table(top5)
bottom_table = df_to_discord_table(bottom5)

# === 📈 Diagramm erstellen ===
plt.figure(figsize=(10, 5))
plt.bar(top5['ticker'], top5['change_percent'], color='green', label='Top 5')
plt.bar(bottom5['ticker'], bottom5['change_percent'], color='red', label='Bottom 5')
plt.xlabel('Ticker')
plt.ylabel('Change %')
plt.title('Top 5 / Bottom 5 Aktien der Stunde')
plt.legend()
plt.tight_layout()
plt.savefig('chart.png')
plt.close()

# === 🤖 Gemini KI Fazit ===
ki_fazit = "⚠️ KI konnte keine Einschätzung generieren."
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        f"Hier sind die Top 5 und Bottom 5 Aktien (mit Preis, Schlusskurs und Veränderung in %):\n\n"
        f"Top 5:\n{top5.to_string(index=False)}\n\n"
        f"Bottom 5:\n{bottom5.to_string(index=False)}\n\n"
        f"Gib eine kurze Marktanalyse mit Fazit und Empfehlung (max. 4 Sätze)."
    )
    response = model.generate_content(prompt)
    ki_fazit = response.text
except Exception as e:
    ki_fazit = f"⚠️ KI konnte nicht antworten: {e}"

# === 📬 Discord Nachricht senden ===
message = (
    "📊 **Top 5 Aktien**\n"
    f"{top_table}\n\n"
    "📉 **Bottom 5 Aktien**\n"
    f"{bottom_table}\n\n"
    f"🤖 **KI Einschätzung**\n{ki_fazit}"
)

webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
webhook.send(content=message, file=File("chart.png"))
