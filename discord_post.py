import json
import os
import pandas as pd
from discord_webhook import DiscordWebhook, DiscordEmbed

# Lade Discord Webhook aus GitHub Secrets (in GitHub Actions verfügbar als Umgebungsvariable)
webhook_url = os.getenv("DISCORD_WEBHOOK")
if not webhook_url:
    raise ValueError("DISCORD_WEBHOOK ist nicht gesetzt!")

# Lade die Daten
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Prüfe fehlende Spalten
required_cols = {"ticker", "price", "previous_close"}
missing_cols = required_cols - set(df.columns)
if missing_cols:
    print(f"Warnung: Fehlende Spalten: {missing_cols}")
    for col in missing_cols:
        df[col] = None  # Spalte mit None füllen

# Fehlende Werte elegant behandeln (nicht 0, sondern "Daten fehlen")
df.fillna({"price": "Daten fehlen", "previous_close": "Daten fehlen"}, inplace=True)

# Berechne Kursänderung nur, wenn Werte numerisch sind
def compute_change(row):
    try:
        return float(row['price']) - float(row['previous_close'])
    except:
        return "Daten fehlen"

df['change'] = df.apply(compute_change, axis=1)

# Bereite Discord-Nachricht vor
webhook = DiscordWebhook(url=webhook_url)

for _, row in df.iterrows():
    ticker = row['ticker']
    price = row['price']
    previous_close = row['previous_close']
    change = row['change']

    embed = DiscordEmbed(title=f"Aktualisierung für {ticker}", color=242424)
    embed.add_embed_field(name="Aktueller Preis", value=str(price))
    embed.add_embed_field(name="Vorheriger Schlusskurs", value=str(previous_close))
    embed.add_embed_field(name="Änderung", value=str(change))

    webhook.add_embed(embed)

# Sende Nachricht
response = webhook.execute()
print("Discord-Nachricht gesendet!")
