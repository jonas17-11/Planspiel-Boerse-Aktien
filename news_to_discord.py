import os
import json
import time
import requests
import feedparser
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Wirtschaftlich relevante RSS-Feeds
RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss",
]

# Schlüsselwörter für extrem wichtige Themen
IMPORTANT_KEYWORDS = [
    "interest rate", "inflation", "recession", "growth", "stock market",
    "earnings", "profit warning", "crash", "AI", "merger", "acquisition",
    "federal reserve", "ECB", "China", "oil prices", "energy crisis",
    "war", "trade", "tariff", "layoffs", "bankruptcy"
]

STATE_FILE = "latest_news_state.json"

def fetch_latest_news(limit_per_feed=10):
    """Liest aktuelle News von RSS-Feeds"""
    news_items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit_per_feed]:
            published = getattr(entry, "published", "")
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "source": feed.feed.get("title", "Unknown"),
                "published": published
            })
    return news_items

def filter_important_news(news_items):
    """Filtert nur extrem wichtige News basierend auf Schlüsselwörtern"""
    important = []
    for n in news_items:
        title_lower = n["title"].lower()
        if any(k in title_lower for k in IMPORTANT_KEYWORDS):
            important.append(n)
    return important

def load_state():
    """Lädt gespeicherte News und letzten Sendezeitpunkt"""
    if not os.path.exists(STATE_FILE):
        return {"sent_titles": [], "last_summary_time": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def get_new_news(news_items, sent_titles):
    """Vergleicht mit alten News, um nur neue zu senden"""
    return [n for n in news_items if n["title"] not in sent_titles]

def generate_ai_summary(news_items, fallback=False):
    """Erstellt ein KI-Fazit mit Gemini"""
    if not GEMINI_API_KEY:
        return "⚠️ Kein GEMINI_API_KEY gefunden. Kein KI-Fazit möglich."

    if fallback:
        prompt = (
            "Erstelle eine kurze, prägnante Zusammenfassung der globalen Wirtschaftslage "
            "basierend auf aktuellen Trends, geopolitischen Entwicklungen und möglichen "
            "Einflüssen auf Aktienmärkte. Maximal 5 Sätze."
        )
    else:
        context = "\n".join([f"- {n['title']} ({n['source']})" for n in news_items])
        prompt = (
            "Analysiere die folgenden extrem wichtigen Wirtschaftsnachrichten. "
            "Erkläre kurz, warum sie relevant für Aktienmärkte sind und welche Branchen besonders betroffen sein könnten. "
            "Fasse dich auf 3–5 Sätze:\n\n" + context
        )

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"

def send_to_discord(message):
    payload = {"content": message}
    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()

def main():
    print("🔍 Lade News ...")
    all_news = fetch_latest_news(limit_per_feed=10)
    important_news = filter_important_news(all_news)

    state = load_state()
    sent_titles = set(state.get("sent_titles", []))
    last_summary_time = state.get("last_summary_time", 0)

    new_important_news = get_new_news(important_news, sent_titles)

    now_ts = time.time()
    twenty_four_hours_ago = now_ts - 24 * 3600
    should_send_summary = last_summary_time < twenty_four_hours_ago

    if not new_important_news and not should_send_summary:
        print("ℹ️ Keine neuen wichtigen News oder tägliche Zusammenfassung nötig.")
        return

    if new_important_news:
        print(f"🆕 {len(new_important_news)} neue wichtige News gefunden.")
        ai_summary = generate_ai_summary(new_important_news)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        message = f"📈 **Neue relevante Finanznews ({now})**\n\n"
        for n in new_important_news[:5]:
            message += f"• **[{n['title']}]({n['link']})**\n🔹 Quelle: {n['source']}\n\n"

        message += f"🤖 **KI-Fazit:**\n{ai_summary}"

        if len(message) > 1900:
            message = message[:1900] + "..."
        send_to_discord(message)
        print("✅ Neue News an Discord gesendet.")
        state["sent_titles"].extend([n["title"] for n in new_important_news])
    elif should_send_summary:
        print("📈 Keine neuen wichtigen News seit 24h — sende globale Zusammenfassung.")
        ai_summary = generate_ai_summary([], fallback=True)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        message = f"🌐 **Tägliche KI-Marktübersicht ({now})**\n\n{ai_summary}"
        send_to_discord(message)
        state["last_summary_time"] = now_ts

    save_state(state)

if __name__ == "__main__":
    main()
