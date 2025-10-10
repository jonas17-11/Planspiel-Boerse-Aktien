import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests

# --- Einstellungen ---
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_WEBHOOK:
    raise ValueError("❌ DISCORD_WEBHOOK ist nicht gesetzt!")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY ist nicht gesetzt!")

# --- Daten laden ---
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)
required_cols = {"ticker", "price", "previous_close"}
for col in required_cols:
    if col not in df.columns:
        df[col] = None

# Prozentuale Änderung berechnen
df["change_pct"] = ((df["price"] - df["previous_close"]) / df["previous_close"]) * 100
df = df.sort_values("change_pct", ascending=False).reset_index(drop=True)

# Top & Flop 5
top5 = df.head(5)
flop5 = df.tail(5).sort_values("change_pct")

# --- Diagramm ---
plt.figure(figsize=(8, 5))
combined = pd.concat([top5, flop5])
colors = ["green" if x > 0 else "red" for x in combined["change_pct"]]
bars = plt.bar(combined["ticker"], combined["change_pct"], color=colors)
plt.title("Top 5 & Flop 5 Aktien – % Veränderung")
plt.ylabel("% Veränderung")
plt.grid(axis="y", linestyle="--", alpha=0.5)

# Prozentwerte auf Balken schreiben
for bar, val in zip(bars, combined["change_pct"]):
    plt.text(bar.get_x() + bar.get_width()/2, val + (0.5 if val >= 0 else -1),
             f"{val:.2f}%", ha="center", va="bottom" if val >= 0 else "top", fontsize=8)

plt.tight_layout()
chart_path = "top_flop_chart.png"
plt.savefig(chart_path, dpi=300)
plt.close()

# --- Tabellen schöner machen ---
def format_table(df, title):
    header = f"**{title}**\n```Ticker | Preis | % Änderung\n----------------------------\n"
    for _, row in df.iterrows():
        header += f"{row['ticker']:<6} | {row['price']:<6.2f} | {row['change_pct']:+.2f}%\n"
    return header + "```"

top_table = format_table(top5, "Top 5 Aktien")
flop_table = format_table(flop5, "Flop 5 Aktien")

# --- Heuristik: Wahrscheinlich steigende Aktien ---
# einfache Regel: moderate + positive Veränderung
likely_to_rise = df[(df["change_pct"] > 0) & (df["change_pct"] < df["change_pct"].quantile(0.75))].head(3)
rise_section = "**Aktien mit steigendem Potenzial:**\n" + ", ".join(likely_to_rise["ticker"].tolist() or ["Keine Kandidaten"])

# --- KI-Fazit (Gemini API) ---
def generate_gemini_fazit(top, flop):
    prompt = f"""
    Du bist ein Finanzanalyst. Analysiere diese Aktienbewegungen.
    Top Aktien: {', '.join(top['ticker'].tolist())}
    Flop Aktien: {', '.join(flop['ticker'].tolist())}
    Gib ein kurzes Fazit auf Deutsch (max. 3 Sätze).
    """
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        response.raise_for_status()
        out = response.json()
        return out["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"

ki_fazit = generate_gemini_fazit(top5, flop5)

# --- Discord Nachricht ---
webhook = DiscordWebhook(url=DISCORD_WEBHOOK)

embed = DiscordEmbed(title="📊 Aktien-Update", color=0x1E90FF)
embed.add_embed_field(name="🏆 Top 5 Aktien", value=top_table, inline=True)
embed.add_embed_field(name="📉 Flop 5 Aktien", value=flop_table, inline=True)
embed.add_embed_field(name="📈 Analyse", value=rise_section, inline=False)
embed.add_embed_field(name="🤖 KI-Fazit", value=ki_fazit, inline=False)

# Chart anhängen
with open(chart_path, "rb") as f:
    webhook.add_file(file=f.read(), filename="top_flop_chart.png")
embed.set_image(url="attachment://top_flop_chart.png")

webhook.add_embed(embed)
webhook.execute()

print("✅ Discord Nachricht erfolgreich gesendet!")
