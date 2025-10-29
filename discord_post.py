import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
from datetime import datetime
import pytz
import yfinance as yf

# === Umgebungsvariablen ===
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not DISCORD_WEBHOOK or not GEMINI_API_KEY:
    raise ValueError("❌ Discord oder Gemini Key fehlt!")

# Zeitzone für Anzeige
TZ_BERLIN = pytz.timezone("Europe/Berlin")
now_berlin = datetime.now(TZ_BERLIN)
update_time_str = now_berlin.strftime("%Y-%m-%d %H:%M:%S")

# Daten laden
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["previous_close"] = pd.to_numeric(df["previous_close"], errors="coerce")
df = df.dropna(subset=["price","previous_close"])
df["change_pct"] = ((df["price"] - df["previous_close"]) / df["previous_close"]) * 100
df = df.sort_values("change_pct", ascending=False).reset_index(drop=True)

top5 = df.head(5)
flop5 = df.tail(5).sort_values("change_pct")

# Diagramm
plt.figure(figsize=(8,5))
combined = pd.concat([top5,flop5])
colors = ["green" if x>0 else "red" for x in combined["change_pct"]]
bars = plt.bar(combined["ticker"], combined["change_pct"], color=colors)
plt.title("Top 5 & Flop 5 Aktien – % Veränderung")
plt.ylabel("% Veränderung")
plt.grid(axis="y", linestyle="--", alpha=0.5)
for bar,val in zip(bars,combined["change_pct"]):
    plt.text(bar.get_x()+bar.get_width()/2, val+(0.5 if val>=0 else -1), f"{val:+.2f}%", ha="center", va="bottom" if val>=0 else "top", fontsize=8)
plt.tight_layout()
chart_path = "top_flop_chart.png"
plt.savefig(chart_path,dpi=300)
plt.close()

# Tabellen
def format_table(df, title):
    header = f"**{title}**\n```Ticker | Preis  | % Änderung\n----------------------------\n"
    for _,row in df.iterrows():
        header += f"{row['ticker']:<6} | {row['price']:<6.2f} | {row['change_pct']:+6.2f}%\n"
    return header+"```"

top_table = format_table(top5,"🏆 Top 5 Aktien")
flop_table = format_table(flop5,"📉 Flop 5 Aktien")

# === Aktien mit steigendem Potenzial (robustes Momentum + Visualisierung) ===
likely_to_rise_list = []

for ticker_symbol in df['ticker']:
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="4d")  # 4 Tage für 3 tägige Veränderungen
        hist = hist['Close'].dropna()
        if len(hist) < 4:
            continue
        daily_changes = hist.pct_change().dropna() * 100
        avg_change = daily_changes[-3:].mean()
        max_loss = min(daily_changes[-3:])
        # Robust: durchschnittlich >0 und max. Rücksetzer < 2%
        if avg_change > 0 and max_loss > -2:
            likely_to_rise_list.append((ticker_symbol, avg_change, daily_changes[-3:].tolist()))
    except Exception:
        continue

# Sortiere nach durchschnittlicher Steigerung, Top 3
likely_to_rise_list.sort(key=lambda x: x[1], reverse=True)
top_rise = likely_to_rise_list[:3]

# Discord-Anzeige mit Mini-Trendvisualisierung
rise_section = "**Aktien mit steigendem Potenzial:**\n"
if top_rise:
    for t in top_rise:
        ticker, avg, changes = t
        trend_str = "".join("▲" if c>0 else "▼" for c in changes)
        rise_section += f"{ticker} (+{avg:.2f}%) {trend_str}\n"
else:
    rise_section += "Keine gefunden."

# KI-Fazit
def generate_gemini_fazit(top,flop):
    prompt = f"Du bist Finanzanalyst. Top: {', '.join(top['ticker'].tolist())}. Flop: {', '.join(flop['ticker'].tolist())}. Kurzes Fazit in Deutsch (max 3 Sätze)."
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
                          headers={"Content-Type":"application/json"},
                          json={"contents":[{"role":"user","parts":[{"text":prompt}]}]},
                          timeout=20)
        r.raise_for_status()
        res = r.json()
        return res["candidates"][0]["content"]["parts"][0]["text"].strip() if res.get("candidates") else "⚠️ Kein KI-Fazit"
    except Exception as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {str(e)}"

ki_fazit = generate_gemini_fazit(top5,flop5)

# Prüfen, ob Daten unverändert
no_change = os.path.exists("no_change.flag")
status_text = "ℹ️ Alte Werte! Nicht darauf hören." if no_change else "✅ Neue Kursdaten verfügbar."

# Discord Nachricht
webhook = DiscordWebhook(url=DISCORD_WEBHOOK)
embed = DiscordEmbed(title=f"📊 Aktien-Update ({update_time_str})", color=0x1E90FF)
embed.add_embed_field(name="Status", value=status_text, inline=False)
embed.add_embed_field(name="🏆 Top 5 Aktien", value=top_table, inline=True)
embed.add_embed_field(name="📉 Flop 5 Aktien", value=flop_table, inline=True)
embed.add_embed_field(name="📈 Analyse", value=rise_section, inline=False)
embed.add_embed_field(name="🤖 KI-Fazit", value=ki_fazit, inline=False)

with open(chart_path,"rb") as f:
    webhook.add_file(file=f.read(), filename="top_flop_chart.png")
embed.set_image(url="attachment://top_flop_chart.png")

webhook.add_embed(embed)
webhook.execute()

print("✅ Discord Nachricht erfolgreich gesendet!")
