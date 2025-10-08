import json
import pandas as pd
from discord_webhook import DiscordWebhook, DiscordEmbed

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

# Optional: fehlende Werte auffüllen, damit Berechnungen nicht fehlschlagen
df.fillna({"price": 0, "previous_close": 0}, inplace=True)

# Beispiel: Berechne Kursänderung
df['change'] = df['price'] - df['previous_close']

# Bereite Discord-Nachricht vor
webhook_url = "DEINE_DISCORD_WEBHOOK_URL"
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
