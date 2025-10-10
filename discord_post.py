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


# === Gemini API Helfer ===
def get_first_available_model():
    """Ruft die verfügbaren Gemini-Modelle ab und gibt den ersten zurück"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        models = response.json().get("models", [])
        if not models:
            raise ValueError("Keine Modelle verfügbar.")
        first_model = models[0]["name"]
        print(f"Verwende Modell: {first_model}")
        return first_model
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fehler beim Abrufen der Modelle: {e}")

def generate_ki_fazit(stocks, model_name):
    stock_names = ", ".join([safe_name(s) for s in stocks])
    content = f"Schreibe ein kurzes KI-Fazit über die Aktien: {stock_names}."
    
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/{model_name}:generateText?key={API_KEY}"
    data = {
        "model": model_name,
        "prompt": [{"type": "text", "content": content}],
        "temperature": 0.7,
        "max_output_tokens": 200
    }
    
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("candidates", [{"content": "⚠️ KI-Fazit konnte nicht abgerufen werden"}])[0]["content"]
    except requests.exceptions.RequestException as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"
    except (KeyError, IndexError):
        return "⚠️ KI-Fazit konnte nicht abgerufen werden: Ungültige Antwort vom Modell"

ki_fazit = generate_ki_fazit(top5, flop5)

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
