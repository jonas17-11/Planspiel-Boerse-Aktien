import requests
import feedparser
import os
from datetime import datetime, timezone

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# RSS-Feeds zu wirtschaftsrelevanten News
RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",          # Wall Street Journal
    "https://www.investing.com/rss/news_25.rss",              # Investing.com
    "https://www.reuters.com/rssFeed/businessNews",           # Reuters
    "https://feeds.bloomberg.com/markets/news.rss"            # Bloomberg
]

# Relevante Stichwörter
KEYWORDS = [
    "stock", "stocks", "share", "market", "markets", "bond", "bonds", "ipo",
    "inflation", "interest rate", "fed", "ecb", "central bank",
    "recession", "growth", "gdp", "oil", "energy", "tech", "ai", "earnings",
    "profit", "quarter", "forecast", "dividend"
]

def fetch_latest_news(limit_per_feed=6):
    """Holt aktuelle News aus mehreren RSS-Feeds"""
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

def filter_relevant_news(news_items):
    """Filtert News nach Aktien- und Wirtschaftsrelevanz"""
    relevant = []
    for n in news_items:
        title_lower = n["title"].lower()
        if any(kw in title_lower for kw in KEYWORDS):
            relevant.append(n)
    return relevant

def generate_ai_summary(news_items):
    """Erstellt ein KI-Fazit mit Gemini"""
    if not GEMINI_API_KEY:
        return "⚠️ Kein GEMINI_API_KEY gefunden. Kein KI-Fazit möglich."

    context = "\n".join([f"- {n['title']} ({n['source']})" for n in news_items])
    prompt = (
        "Hier sind aktuelle Wirtschafts- und Finanznachrichten. "
        "Fasse sie prägnant zusammen und erkläre mögliche Auswirkungen auf die Aktienmärkte. "
        "Nutze maximal 5 Sätze:\n\n" + context
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
        result = resp.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"

def format_discord_message(news_items, ai_summary, filtered):
    """Formatiert Discord-Nachricht"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if filtered:
        header = f"📈 **Relevante Finanznews ({now})**\n\n"
    else:
        header = f"📰 **Allgemeine Wirtschaftsnews ({now})**\n\n"

    content = header
    for n in news_items:
        content += f"• **[{n['title']}]({n['link']})**\n"
        content += f"  🔹 Quelle: {n['source']}\n\n"

    content += f"🤖 **KI-Fazit:**\n{ai_summary}\n"
    return content[:1900]

def send_to_discord(message):
    """Sendet Nachricht an Discord"""
    payload = {"content": message}
    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()
    print("✅ News erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    try:
        all_news = fetch_latest_news(limit_per_feed=6)
        relevant_news = filter_relevant_news(all_news)

        # Falls keine relevanten gefunden → normale News verwenden
        if relevant_news:
            print(f"🔍 {len(relevant_news)} relevante News gefunden.")
            used_news = relevant_news[:5]
            filtered = True
        else:
            print("ℹ️ Keine spezifisch relevanten News gefunden – sende allgemeine.")
            used_news = all_news[:5]
            filtered = False

        ai_summary = generate_ai_summary(used_news)
        msg = format_discord_message(used_news, ai_summary, filtered)
        send_to_discord(msg)
    except Exception as e:
        print(f"⚠️ Fehler beim Ausführen: {e}")
