import os
import json
import time
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.reuters.com/rssFeed/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss",
]

IMPORTANT_KEYWORDS = [
    "interest rate", "inflation", "recession", "growth", "stock market",
    "earnings", "profit warning", "crash", "AI", "merger", "acquisition",
    "federal reserve", "ECB", "China", "oil prices", "energy crisis",
    "war", "trade", "tariff", "layoffs", "bankruptcy"
]

STATE_FILE = "latest_news_state.json"


def parse_pub_date(entry):
    """Versucht, ein Datum aus RSS zu lesen und in UTC umzuwandeln"""
    try:
        if hasattr(entry, "published"):
            dt = parsedate_to_datetime(entry.published)
            return dt.astimezone(timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)


def fetch_latest_news(limit_per_feed=10, max_age_hours=48):
    """Liest aktuelle News, filtert alte (>48h) heraus"""
    news_items = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit_per_feed]:
            pub_date = parse_pub_date(entry)
            if pub_date < cutoff_time:
                continue  # alte News überspringen
            news_items.append({
                "title": entry.title.strip(),
                "link": entry.link,
                "source": feed.feed.get("title", "Unknown"),
                "published": pub_date.isoformat()
            })
    return news_items


def filter_important_news(news_items):
    important = []
    for n in news_items:
        title_lower = n["title"].lower()
        if any(k in title_lower for k in IMPORTANT_KEYWORDS):
            important.append(n)
    return important


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent_titles": {}, "last_summary_time": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clean_old_titles(state, max_age_days=5):
    """Löscht alte Titel aus der Historie nach x Tagen"""
    now_ts = time.time()
    new_sent_titles = {
        title: ts for title, ts in state.get("sent_titles", {}).items()
        if now_ts - ts < max_age_days * 86400
    }
    removed = len(state.get("sent_titles", {})) - len(new_sent_titles)
    if removed > 0:
        print(f"🧹 {removed} alte gespeicherte Titel entfernt.")
    state["sent_titles"] = new_sent_titles


def get_new_news(news_items, sent_titles):
    """Nur News, die noch nicht gesendet wurden"""
    return [n for n in news_items if n["title"] not in sent_titles]


def generate_ai_summary(news_items, fallback=False):
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
    clean_old_titles(state)
    sent_titles = state.get("sent_titles", {})
    last_summary_time = state.get("last_summary_time", 0)

    new_important_news = get_new_news(important_news, sent_titles)
    now_ts = time.time()
    should_send_summary = now_ts - last_summary_time > 24 * 3600

    if not new_important_news and not should_send_summary:
        print("ℹ️ Keine neuen wichtigen News oder tägliche Zusammenfassung nötig.")
        save_state(state)
        return

    if new_important_news:
        print(f"🆕 {len(new_important_news)} neue wichtige News gefunden.")
        ai_summary = generate_ai_summary(new_important_news)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        message = f"🌍 **Extrem wichtige Wirtschaftsnachrichten ({now})**\n\n"
        for n in new_important_news[:5]:
            message += f"• **[{n['title']}]({n['link']})**\n🔹 Quelle: {n['source']}\n\n"
        message += f"🤖 **KI-Fazit:**\n{ai_summary}"

        if len(message) > 1900:
            message = message[:1900] + "..."
        send_to_discord(message)
        print("✅ Neue News an Discord gesendet.")

        for n in new_important_news:
            sent_titles[n["title"]] = now_ts

    elif should_send_summary:
        print("📈 Keine neuen wichtigen News seit 24h — sende globale Zusammenfassung.")
        ai_summary = generate_ai_summary([], fallback=True)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        message = f"🌐 **Tägliche KI-Marktübersicht ({now})**\n\n{ai_summary}"
        send_to_discord(message)
        state["last_summary_time"] = now_ts

    state["sent_titles"] = sent_titles
    save_state(state)


if __name__ == "__main__":
    main()
