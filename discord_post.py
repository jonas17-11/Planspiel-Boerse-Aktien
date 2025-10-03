import os, json, requests
from discord import Webhook, RequestsWebhookAdapter

# GitHub Secrets via Environment Variables
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
RAW_JSON_URL = os.environ["RAW_JSON_URL"]

# JSON von GitHub laden
r = requests.get(RAW_JSON_URL)
data = r.json()["data"]

# Top 10 Gewinner & Flop 5 Verlierer
data_sorted = sorted(data, key=lambda x: x['percent_change'], reverse=True)
top10 = data_sorted[:10]
flop5 = data_sorted[-5:]

# Nachricht formatieren
msg = "**📈 Top 10 Gewinner der Stunde:**\n"
msg += "\n".join([f"{d['ticker']}: {d['percent_change']}%" for d in top10])
msg += "\n\n**📉 Top 5 Verlierer der Stunde:**\n"
msg += "\n".join([f"{d['ticker']}: {d['percent_change']}%" for d in flop5])

# Nachricht senden
webhook = Webhook.from_url(WEBHOOK_URL, adapter=RequestsWebhookAdapter())
webhook.send(msg)
