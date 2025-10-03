#!/usr/bin/env python3
# discord_bot.py
import os
import requests
import pandas as pd
import discord
from discord.ext import tasks, commands
from tabulate import tabulate
import io
import matplotlib.pyplot as plt
import yfinance as yf
import openai
from datetime import datetime

# ==== KONFIG über Umgebungsvariablen (sicher speichern) ====
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")            # Discord Bot Token
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")          # OpenAI API Key
CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))  # Channel-ID (als int)
RAW_JSON_URL = os.environ.get("RAW_JSON_URL")              # z.B. https://raw.githubusercontent.com/..../monitor_output.json

if not (DISCORD_TOKEN and OPENAI_API_KEY and CHANNEL_ID and RAW_JSON_URL):
    raise SystemExit("Set DISCORD_TOKEN, OPENAI_API_KEY, DISCORD_CHANNEL_ID and RAW_JSON_URL as environment variables")

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_json():
    r = requests.get(RAW_JSON_URL, timeout=20)
    r.raise_for_status()
    js = r.json()
    # handle shape: { "timestamp": ..., "data": [ {...}, ... ] }
    if isinstance(js, dict) and "data" in js:
        data = js["data"]
    elif isinstance(js, list):
        data = js
    else:
        # try to convert dict-of-objects to list
        if isinstance(js, dict):
            # maybe flat map; convert to list
            data = []
            for k, v in js.items():
                if isinstance(v, dict):
                    v["ticker"] = k
                    data.append(v)
        else:
            raise ValueError("Unbekanntes JSON-Format")
    df = pd.DataFrame(data)
    # normalize column names
    df.columns = [c if isinstance(c, str) else str(c) for c in df.columns]
    # Expect columns: ticker, price, percent_change
    if "ticker" not in df.columns and "symbol" in df.columns:
        df = df.rename(columns={"symbol":"ticker"})
    return df

def make_plot(tickers):
    plt.style.use('seaborn-v0_8') if 'seaborn-v0_8' in plt.style.available else None
    plt.figure(figsize=(8,4))
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period="7d", interval="1h")
            if hist.empty:
                continue
            plt.plot(hist.index, hist["Close"], label=t)
        except Exception as e:
            print("Plot Fehler", t, e)
    plt.legend()
    plt.title("7-Tage Verlauf (stündlich)")
    plt.xlabel("")
    plt.xticks(rotation=30)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

def ask_ai(top10_df, flop5_df):
    prompt = f"""Du bist ein sachlicher Finanz-Assistent. 
Analysiere kurz (Deutsch, max. 6 Sätze) die folgende Momentaufnahme, nenne mögliche Gründe für Auf- oder Abwärtsbewegungen und zwei kurze hypothetische Erwägungen, ob ein Trader diese Aktien näher untersuchen sollte. Keine Anlageberatung, nur Hypothesen.

Top 10 (Ticker | Preis | %Δ):
{top10_df.to_string(index=False)}

Flop 5 (Ticker | Preis | %Δ):
{flop5_df.to_string(index=False)}
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":"Du bist ein Finanzanalyse-Assistent."},
            {"role":"user","content":prompt}
        ],
        max_tokens=300,
        temperature=0.7
    )
    text = resp.choices[0].message.content.strip()
    return text

@tasks.loop(hours=1)
async def hourly_post():
    try:
        df = fetch_json()
        if df.empty:
            print("Keine Daten im JSON.")
            return
        # Make sure columns exist
        for col in ["ticker","price","percent_change"]:
            if col not in df.columns:
                raise ValueError(f"JSON fehlt required field: {col}")

        df = df.dropna(subset=["ticker","price"]).copy()
        # percent_change numeric
        df["percent_change"] = pd.to_numeric(df["percent_change"], errors="coerce").fillna(0.0)
        df = df.sort_values("percent_change", ascending=False)

        top10 = df.head(10)[["ticker","price","percent_change"]]
        flop5 = df.tail(5)[["ticker","price","percent_change"]]

        # Tabellen als codeblock
        table_top = "```\n" + tabulate(top10, headers=["Ticker","Preis","% Δ"], tablefmt="pretty", showindex=False) + "\n```"
        table_flop = "```\n" + tabulate(flop5, headers=["Ticker","Preis","% Δ"], tablefmt="pretty", showindex=False) + "\n```"

        # Chart für die Top 3 Gewinner
        top_tickers = list(top10["ticker"].head(3))
        chart_buf = make_plot(top_tickers) if top_tickers else None

        ai_text = ask_ai(top10, flop5)

        embed = discord.Embed(title="📊 Stündliches Aktien-Update", description=f"Stand: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        embed.add_field(name="Top 10 (Stunde)", value=table_top, inline=False)
        embed.add_field(name="Bottom 5 (Stunde)", value=table_flop, inline=False)
        embed.add_field(name="🤖 KI-Einschätzung (Hypothesen)", value=ai_text, inline=False)

        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(CHANNEL_ID)

        if chart_buf:
            file = discord.File(chart_buf, filename="chart.png")
            embed.set_image(url="attachment://chart.png")
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)

    except Exception as e:
        print("Fehler beim Posten:", e)
        channel = bot.get_channel(CHANNEL_ID) or await bot.fetch_channel(CHANNEL_ID)
        await channel.send(f"⚠️ Fehler beim Abrufen/Verarbeiten: `{e}`")

@bot.command(name="now")
@commands.is_owner()
async def now_cmd(ctx):
    """Manueller Trigger: Sendet sofort ein Update (nur Botowner)."""
    await ctx.send("Manueller Update-Trigger gestartet...")
    await hourly_post()

@bot.event
async def on_ready():
    print("Bot ready:", bot.user)
    if not hourly_post.is_running():
        hourly_post.start()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
