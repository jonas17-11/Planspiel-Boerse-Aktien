import requests
import feedparser
import os
from datetime import datetime, timezone

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss"
]

def fetch_latest_news(limit_per_feed=3):
    news_items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit_per_feed]:
            published = getattr(entry, "published", "")
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "source": feed.feed.get("title", "Unbekannte Quelle"),
                "published": published
            })
    return news_items

def generate_ai_summary(news_items):
    """Erstellt ein KI-Fazit mit Gemini"""
    if not GEMINI_API_KEY:
        return "⚠️ Kein GEMINI_API_KEY gefunden. Kein KI-Fazit möglich."

    # Text für die KI vorbereiten
    context = "\n".join([f"- {n['title']} ({n['source']})" for n in news_items])
    prompt = (
        "Fasse die folgenden aktuellen Wirtschaftsnachrichten kurz zusammen und erkläre, "
        "welche möglichen Auswirkungen sie auf die Aktienmärkte haben könnten. "
        "Sei prägnant (max. 5 Sätze):\n\n" + context
    )

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        resp = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        resp.raise_for_status()
        response_json = resp.json()
        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"

def format_discord_message(news_items, ai_summary):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = f"📰 **Aktuelle Wirtschaftsnews ({now})**\n\n"
    for n in news_items:
        content += f"• **[{n['title']}]({n['link']})**\n"
        content += f"  🔹 Quelle: {n['source']}\n\n"

    content += f"🤖 **KI-Fazit:**\n{ai_summary}\n"
    return content[:1900]

def send_to_discord(message):
    payload = {"content": message}
    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()
    print("✅ News erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    try:
        news = fetch_latest_news(limit_per_feed=3)
        ai_summary = generate_ai_summary(news)
        msg = format_discord_message(news, ai_summary)
        send_to_discord(msg)
    except Exception as e:
        print(f"⚠️ Fehler beim Ausführen: {e}")
