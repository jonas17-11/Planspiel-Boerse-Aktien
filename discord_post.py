import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests

# Lade Discord Webhook aus GitHub Secrets
webhook_url = os.getenv("DISCORD_WEBHOOK")
if not webhook_url:
    raise ValueError("DISCORD_WEBHOOK ist nicht gesetzt!")

# Lade Gemini API Key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY ist nicht gesetzt!")

# Lade die Daten
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Prüfe und ergänze fehlende Spalten
required_cols = {"ticker", "price", "previous_close"}
for col in required_cols:
    if col not in df.columns:
        df[col] = None

# Berechne Kursänderung in Prozent
def compute_change_pct(row):
    try:
        return round((float(row['price']) - float(row['previous_close'])) / float(row['previous_close']) * 100, 2)
    except:
        return 0

df['change_pct'] = df.apply(compute_change_pct, axis=1)

# Top 5 und Flop 5 Aktien
top5 = df.sort_values(by='change_pct', ascending=False).head(5)
flop5 = df.sort_values(by='change_pct').head(5)

# Markdown-Tabellen für Discord
def create_table(df_subset, title):
    table = f"**{title}**\n```\nTicker   Preis   % Änderung\n"
    for _, row in df_subset.iterrows():
        table += f"{row['ticker']:<7} {row['price']:<7} {row['change_pct']}%\n"
    table += "```"
    return table

top_table = create_table(top5, "Top 5 Aktien")
flop_table = create_table(flop5, "Flop 5 Aktien")

# Diagramm erstellen
plt.figure(figsize=(10,5))
plt.bar(df['ticker'], df['change_pct'], color=['green' if x>=0 else 'red' for x in df['change_pct']])
plt.xlabel("Ticker")
plt.ylabel("% Änderung")
plt.title("Aktienkursänderungen")
plt.tight_layout()
chart_file = "chart.png"
plt.savefig(chart_file)
plt.close()

# KI-Fazit generieren via Gemini API
def generate_ki_fazit(top, flop):
    prompt = f"Schreibe ein kurzes Fazit über die Aktienperformance:\nTop Aktien: {', '.join(top['ticker'].tolist())}\nSchlechteste Aktien: {', '.join(flop['ticker'].tolist())}"
    headers = {"Authorization": f"Bearer {gemini_api_key}"}
    response = requests.post(
        "https://api.gemini.com/v1/ai/generate",
        headers=headers,
        json={"prompt": prompt, "max_tokens": 100}
    )
    if response.status_code == 200:
        return response.json().get("text", "Keine Antwort von KI")
    else:
        return f"KI-Fazit konnte nicht abgerufen werden (Status {response.status_code})"

ki_fazit = generate_ki_fazit(top5, flop5)

# Discord Nachricht vorbereiten
webhook = DiscordWebhook(url=webhook_url)

# Tabelle und KI-Fazit
embed = DiscordEmbed(title="Aktien Update", color=242424)
embed.add_embed_field(name="Top 5 Aktien", value=top_table)
embed.add_embed_field(name="Flop 5 Aktien", value=flop_table)
embed.add_embed_field(name="KI Fazit", value=ki_fazit)
webhook.add_embed(embed)

# Diagramm anhängen
with open(chart_file, "rb") as f:
    webhook.add_file(file=f.read(), filename=chart_file)

# Senden
response = webhook.execute()
print("Discord Update gesendet!")
