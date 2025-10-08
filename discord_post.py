import json
import os
import pandas as pd
from discord_webhook import DiscordWebhook, DiscordEmbed

# Lade Discord Webhook aus GitHub Secrets
webhook_url = os.getenv("DISCORD_WEBHOOK")
if not webhook_url:
    raise ValueError("DISCORD_WEBHOOK ist nicht gesetzt! Bitte als Secret im GitHub Repo hinzufügen.")

# Lade die Daten
try:
    with open("monitor_output.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError("monitor_output.json nicht gefunden! Bitte zuerst monitor.py ausführen.")

df = pd.DataFrame(data)

# Prüfe fehlende Spalten und füge sie ggf. hinzu
required_cols = {"ticker", "price", "previous_close"}
missing_cols = required_cols - set(df.columns)
if missing_cols:
    print(f"Warnung: Fehlende Spalten: {missing_cols}")
    for col in missing_cols:
        df[col] = None

# Fehlende Werte elegant behandeln
df.fillna({"price": "Daten fehlen", "previous_close": "Daten fehlen"}, inplace=True)

# Berechne Kursänderung nur, wenn Werte numerisch sind
def compute_change(row):
    try:
        return round(float(row['price']) - float(row['previous_close']), 2)
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
