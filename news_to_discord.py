import requests
import feedparser
import os
import json
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STATE_FILE = "last_news.json"

# RSS-Feeds
RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss"
]

# Schlüsselwörter für relevante Finanz-News
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
            published_parsed = getattr(entry, "published_parsed", None)
            timestamp = None
            if published_parsed:
                timestamp = datetime(*published_parsed[:6]).replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "source": feed.feed.get("title", "Unbekannte Quelle"),
                "published": published,
                "timestamp": timestamp
            })
    return news_items


def load_last_state():
    """Lädt gespeicherte News"""
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_current_state(news_list):
    """Speichert aktuelle News-Liste"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)


def clean_old_entries(news_list, hours=48):
    """Entfernt Einträge, die älter als X Stunden sind"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    fresh = []
    for n in news_list:
        try:
            ts = datetime.fromisoformat(n["timestamp"])
            if ts > cutoff:
                fresh.append(n)
        except Exception:
            pass
    return fresh


def filter_new_news(news_items, old_links):
    """Filtert nur neue Artikel"""
    old_urls = {n["link"] for n in old_links}
    return [n for n in news_items if n["link"] not in old_urls]


def filter_relevant_news(news_items):
    """Filtert News nach Stichwörtern"""
    relevant = []
    for n in news_items:
        title_lower = n["title"].lower()
        if any(kw in title_lower for kw in KEYWORDS):
            relevant.append(n)
    return relevant


def generate_ai_summary(news_items):
    """Erstellt ein KI-Fazit mit Gemini auf Deutsch"""
    if not GEMINI_API_KEY:
        return "⚠️ Kein GEMINI_API_KEY gefunden."

    context = "\n".join([f"- {n['title']} ({n['source']})" for n in news_items])
    prompt = (
        "Hier sind aktuelle Wirtschafts- und Finanznachrichten. "
        "Fasse sie auf **Deutsch** zusammen und erkläre in höchstens 5 Sätzen, "
        "wie sie sich auf die Aktienmärkte auswirken könnten:\n\n" + context
    )

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except Exception as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"


def format_discord_message(news_items, ai_summary, total_count, relevant_count, filtered):
    """Formatiert Discord-Nachricht"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if filtered:
        header = f"📈 **Neue relevante Finanznews ({now})**\n\n"
    else:
        header = f"📰 **Neue allgemeine Wirtschaftsnews ({now})**\n\n"

    content = header
    for n in news_items:
        content += f"• **[{n['title']}]({n['link']})**\n"
        content += f"  🔹 Quelle: {n['source']}\n\n"

    content += f"🤖 **KI-Fazit:**\n{ai_summary}\n\n"
    content += f"📊 **Statistik:** {total_count} Artikel gescannt, {relevant_count} relevant, {len(news_items)} neu gefunden."
    return content[:1900]


def send_to_discord(message):
    """Sendet Nachricht an Discord"""
    payload = {"content": message}
    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()
    print("✅ Nachricht erfolgreich an Discord gesendet.")


if __name__ == "__main__":
    try:
        all_news = fetch_latest_news(limit_per_feed=6)
        old_state = load_last_state()
        old_state = clean_old_entries(old_state, hours=48)

        new_news = filter_new_news(all_news, old_state)
        if not new_news:
            print("ℹ️ Keine neuen News seit letztem Lauf.")
            save_current_state(old_state)
            exit(0)

        relevant_news = filter_relevant_news(new_news)

        total_count = len(all_news)
        relevant_count = len(relevant_news)

        if relevant_news:
            used_news = relevant_news[:5]
            filtered = True
        else:
            used_news = new_news[:5]
            filtered = False

        ai_summary = generate_ai_summary(used_news)
        msg = format_discord_message(used_news, ai_summary, total_count, relevant_count, filtered)
        send_to_discord(msg)

        # Speichere neue Artikel + alte (nur aktuelle)
        updated_state = old_state + used_news
        updated_state = clean_old_entries(updated_state, hours=48)
        save_current_state(updated_state)

    except Exception as e:
        print(f"⚠️ Fehler beim Ausführen: {e}")
