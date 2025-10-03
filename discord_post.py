import os, json, requests
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed

# Hugging Face
HF_API_KEY = os.environ["HF_API_KEY"]
HF_MODEL = "EleutherAI/gpt-neo-1.3B"

# Discord & GitHub
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
RAW_JSON_URL = os.environ["RAW_JSON_URL"]

# JSON von GitHub laden
r = requests.get(RAW_JSON_URL)
data = r.json()["data"]

# DataFrame
df = pd.DataFrame(data)
df['percent_change'] = pd.to_numeric(df['percent_change'])
df['price'] = pd.to_numeric(df['price'])

# Top/Flop
df_sorted = df.sort_values(by='percent_change', ascending=False)
top10 = df_sorted.head(10)
flop5 = df_sorted.tail(5)

# Nachricht formatieren
msg = "**📈 Top 10 Gewinner der Stunde:**\n"
for _, row in top10.iterrows():
    msg += f"{row['ticker']}: {row['price']} USD ({row['percent_change']}%)\n"

msg += "\n**📉 Top 5 Verlierer der Stunde:**\n"
for _, row in flop5.iterrows():
    msg += f"{row['ticker']}: {row['price']} USD ({row['percent_change']}%)\n"

# Diagramm
fig, ax = plt.subplots(figsize=(10,5))
top3 = df_sorted.head(3)
ax.bar(top3['ticker'], top3['percent_change'], color='green', label='Top 3 Gewinner')
ax.bar(flop5['ticker'], flop5['percent_change'], color='red', label='Flop 5 Verlierer')
ax.set_ylabel('Prozentuale Veränderung (%)')
ax.set_title('Top 3 Gewinner vs Flop 5 Verlierer der Stunde')
ax.legend()
plt.tight_layout()
chart_file = "combined_chart.png"
plt.savefig(chart_file)
plt.close()

# Discord vorbereiten
webhook = DiscordWebhook(url=WEBHOOK_URL, content=msg)
with open(chart_file, "rb") as f:
    webhook.add_file(file=f.read(), filename="combined_chart.png")

# KI-Fazit via Hugging Face
try:
    prompt = f"""
Hier sind die Top 10 Gewinner und Top 5 Verlierer der letzten Stunde:
Gewinner: {', '.join(top10['ticker'].tolist())}
Verlierer: {', '.join(flop5['ticker'].tolist())}

Schreibe eine kurze Einschätzung (3-4 Sätze), welche Aktien interessant sein könnten. Nur Hypothese, keine Finanzberatung.
"""
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_MODEL}",
        headers=headers,
        json={"inputs": prompt, "parameters": {"max_new_tokens": 150}}
    )

    # Sicherstellen, dass wir Text aus der Antwort extrahieren
    hf_json = response.json()
    if isinstance(hf_json, list) and 'generated_text' in hf_json[0]:
        ki_fazit = hf_json[0]['generated_text'].strip()
    else:
        ki_fazit = "⚠️ KI-Fazit konnte nicht erstellt werden."

    embed = DiscordEmbed(title="💡 KI Einschätzung", description=ki_fazit, color=0x00ff00)
    webhook.add_embed(embed)

except Exception as e:
    print(f"⚠️ KI-Fazit konnte nicht erstellt werden: {e}")
    embed = DiscordEmbed(title="💡 KI Einschätzung", description="⚠️ KI-Fazit konnte nicht erstellt werden.", color=0xff0000)
    webhook.add_embed(embed)

# Nachricht senden
webhook.execute()
