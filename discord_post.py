import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests

# === Umgebungsvariablen ===
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_WEBHOOK:
    raise ValueError("❌ DISCORD_WEBHOOK ist nicht gesetzt!")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY ist nicht gesetzt!")

# === Daten laden ===
with open("monitor_output.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Fehlende Spalten absichern
required_cols = {"ticker", "price", "previous_close"}
for col in required_cols:
    if col not in df.columns:
        df[col] = None

# Konvertiere Zahlen
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["previous_close"] = pd.to_numeric(df["previous_close"], errors="coerce")

# Entferne Zeilen ohne gültige Werte
df = df.dropna(subset=["price", "previous_close"])

# Kursänderung in %
df["change_pct"] = ((df["price"] - df["previous_close"]) / df["previous_close"]) * 100
df = df.sort_values("change_pct", ascending=False).reset_index(drop=True)

# Top & Flop 5
top5 = df.head(5)
flop5 = df.tail(5).sort_values("change_pct")

# === Diagramm: Top & Flop 5 ===
plt.figure(figsize=(8, 5))
combined = pd.concat([top5, flop5])
colors = ["green" if x > 0 else "red" for x in combined["change_pct"]]

bars = plt.bar(combined["ticker"], combined["change_pct"], color=colors)
plt.title("Top 5 & Flop 5 Aktien – % Veränderung")
plt.ylabel("% Veränderung")
plt.grid(axis="y", linestyle="--", alpha=0.5)

# Prozentwerte über Balken schreiben
for bar, val in zip(bars, combined["change_pct"]):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        val + (0.5 if val >= 0 else -1),
        f"{val:+.2f}%",
        ha="center",
        va="bottom" if val >= 0 else "top",
        fontsize=8,
    )

plt.tight_layout()
chart_path = "top_flop_chart.png"
plt.savefig(chart_path, dpi=300)
plt.close()

# === Tabellen schöner formatieren ===
def format_table(df, title):
    header = f"**{title}**\n```Ticker | Preis  | % Änderung\n----------------------------\n"
    for _, row in df.iterrows():
        header += f"{row['ticker']:<6} | {row['price']:<6.2f} | {row['change_pct']:+6.2f}%\n"
    return header + "```"

top_table = format_table(top5, "🏆 Top 5 Aktien")
flop_table = format_table(flop5, "📉 Flop 5 Aktien")

# === Heuristik: 3 Aktien mit Potenzial ===
# Immer 3 beste positive Aktien anzeigen (ohne Wiederholung)
likely_to_rise = df[df["change_pct"] > 0].nlargest(3, "change_pct")
if likely_to_rise.empty:
    rise_section = "**Aktien mit steigendem Potenzial:** Keine gefunden."
else:
    rise_section = "**Aktien mit steigendem Potenzial:**\n" + ", ".join(
        [f"{row['ticker']} (+{row['change_pct']:.2f}%)" for _, row in likely_to_rise.iterrows()]
    )


# === KI-Fazit mit Gemini 1.5 Pro ===
def generate_gemini_fazit(top, flop):
    """
    Generiert ein kurzes Finanzfazit für Top- und Flop-Aktien.
    Gibt immer einen String zurück, auch bei Fehlern.
    """
    prompt = f"""
    Du bist ein Finanzanalyst. Analysiere die heutigen Kursänderungen.
    Top Aktien: {', '.join(top['ticker'].tolist())}
    Flop Aktien: {', '.join(flop['ticker'].tolist())}
    Gib ein kurzes, verständliches Fazit auf Deutsch (max. 3 Sätze).
    """

    ki_fazit = "⚠️ KI-Fazit konnte nicht abgerufen werden."  # Default-Wert

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateText?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ]
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        # Prüfen, ob die Antwort korrekt ist
        if result.get("candidates") and len(result["candidates"]) > 0:
            ki_fazit = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        ki_fazit = f"⚠️ KI-Fazit konnte nicht abgerufen werden: {str(e)}"

    return ki_fazit

# === Discord Embed mit KI-Fazit ===
top = get_top_stocks()      # deine Funktion, die Top-Aktien liefert
flop = get_flop_stocks()    # deine Funktion, die Flop-Aktien liefert

# KI-Fazit generieren
ki_fazit = generate_gemini_fazit(top, flop)

# Embed erstellen
embed = discord.Embed(
    title="📊 Tagesauswertung der Aktien",
    description="Hier ist die Auswertung der Top- und Flop-Aktien von heute",
    color=0x00ff00
)
embed.add_embed_field(name="🤖 KI-Fazit", value=ki_fazit, inline=False)

# Restlicher Embed-Code hier, z.B. senden via webhook
send_discord_embed(embed)


# === Discord Nachricht ===
webhook = DiscordWebhook(url=DISCORD_WEBHOOK)

embed = DiscordEmbed(title="📊 Aktien-Update", color=0x1E90FF)
embed.add_embed_field(name="🏆 Top 5 Aktien", value=top_table, inline=True)
embed.add_embed_field(name="📉 Flop 5 Aktien", value=flop_table, inline=True)
embed.add_embed_field(name="📈 Analyse", value=rise_section, inline=False)
embed.add_embed_field(name="🤖 KI-Fazit", value=ki_fazit, inline=False)

# Chart anhängen & einbinden
with open(chart_path, "rb") as f:
    webhook.add_file(file=f.read(), filename="top_flop_chart.png")
embed.set_image(url="attachment://top_flop_chart.png")

webhook.add_embed(embed)

# Nur EINMAL senden
webhook.execute()

print("✅ Discord Nachricht erfolgreich gesendet!")
