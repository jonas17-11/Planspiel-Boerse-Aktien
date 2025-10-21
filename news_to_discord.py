import requests
import feedparser
import os
from datetime import datetime, timezone

# Discord Webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# RSS-Feeds zu wirtschaftsrelevanten News
RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",          # Wall Street Journal Markets
    "https://www.investing.com/rss/news_25.rss",              # Investing.com - Wirtschaft
    "https://www.reuters.com/rssFeed/businessNews",           # Reuters Business
    "https://feeds.bloomberg.com/markets/news.rss"            # Bloomberg Markets
]

def fetch_latest_news(limit_per_feed=3):
    """Holt aktuelle News aus mehreren RSS-Feeds"""
    news_items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit_per_feed]:
            published = getattr(entry, "published", None)
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "source": feed.feed.get("title", "Unbekannte Quelle"),
                "published": published
            })
    return news_items

def format_discord_message(news_items):
    """Formatiert die Nachricht für Discord"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = f"📰 **Aktuelle Wirtschaftsnews ({now})**\n\n"
    
    for n in news_items:
        content += f"• **[{n['title']}]({n['link']})**\n"
        content += f"  🔹 Quelle: {n['source']}\n\n"

    return content[:1900]  # Discord max 2000 Zeichen

def send_to_discord(message):
    """Sendet Nachricht an Discord"""
    payload = {"content": message}
    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()
    print("✅ News erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    try:
        news = fetch_latest_news(limit_per_feed=3)
        msg = format_discord_message(news)
        send_to_discord(msg)
    except Exception as e:
        print(f"⚠️ Fehler beim Senden: {e}")
