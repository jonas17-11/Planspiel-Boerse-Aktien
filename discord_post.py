import os, json, requests
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed
import openai

# Secrets aus GitHub Actions
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
RAW_JSON_URL = os.environ["RAW_JSON_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

openai.api_key = OPENAI_API_KEY

# JSON von GitHub laden
r = requests.get(RAW_JSON_URL)
data = r.json()["data"]

# DataFrame für einfache Verarbeitung
df = pd.DataFrame(data)
df['percent_change'] = pd.to_numeric(df['percent_change'])

# Top 10 Gewinner & Flop 5 Verlierer
df_sorted = df.sort_values(by='percent_change', ascending=False)
top10 = df_sorted.head(10)
flop5 = df_sorted.tail(5)

# Nachricht formatieren (Ticker, Preis, Veränderung)
msg = "**📈 Top 10 Gewinner der Stunde:**\n"
for _, row in top10.iterrows():
    msg += f"{row['ticker']}: {row['price']} USD ({row['percent_change']}%)\n"

msg += "\n**📉 Top 5 Verlierer der Stunde:**\n"
for _, row in flop5.iterrows():
    msg += f"{row['ticker']}: {row['price']} USD ({row['percent_change']}%)\n"

# Diagramme für Top 3 Gewinner
plt.figure(figsize=(6,4))
top3 = df_sorted.head(3)
plt.bar(top3['ticker'], top3['percent_change'], color='green')
plt.ylabel('Prozentuale Veränderung (%)')
plt.title('Top 3 Gewinner der Stunde')
plt.tight_layout()
chart_file = "top3_chart.png"
plt.savefig(chart_file)
plt.close()

# KI Fazit generieren
top_tickers = ', '.join(top10['ticker'].tolist())
flop_tickers = ', '.join(flop5['ticker'].tolist())
prompt = f"""
Hier sind die Top 10 Gewinner und Top 5 Verlierer der letzten Stunde im Börsenplanspiel:
Gewinner: {top_tickers}
Verlierer: {flop_tickers}

Bitte schreibe eine kurze Einschätzung (3-4 Sätze) welche Aktien interessant sein könnten, basierend auf der Bewegung, nur Hypothese, keine Finanzberatung.
"""

response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=prompt,
    max_tokens=150
)
ki_fazit = response.choices[0].text.strip()

# Discord Nachricht senden
webhook = DiscordWebhook(url=WEBHOOK_URL, content=msg)
# Bild hinzufügen
with open(chart_file, "rb") as f:
    webhook.add_file(file=f.read(), filename="top3_chart.png")

# KI-Fazit als Embed
embed = DiscordEmbed(title="💡 KI Einschätzung", description=ki_fazit, color=0x00ff00)
webhook.add_embed(embed)

webhook.execute()
