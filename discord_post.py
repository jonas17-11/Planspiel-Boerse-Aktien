import json
import os
import requests
import matplotlib.pyplot as plt
from io import BytesIO

# === CONFIG aus Secrets ===
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"  # Aktualisiertes Modell

# Pfad zur JSON-Datei im Root-Verzeichnis
MONITOR_OUTPUT_FILE = os.path.join(os.getcwd(), "monitor-output.json")

# Secrets prüfen
if not DISCORD_WEBHOOK_URL or not API_KEY:
    raise ValueError("Bitte stelle sicher, dass DISCORD_WEBHOOK und GEMINI_API_KEY gesetzt sind!")

# Datei prüfen oder leere Liste anlegen, falls fehlt
if not os.path.exists(MONITOR_OUTPUT_FILE):
    print(f"Warnung: {MONITOR_OUTPUT_FILE} nicht gefunden. Erstelle Dummy-Datei.")
    with open(MONITOR_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# === Hilfsfunktionen ===
def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_get(stock, key, default=0):
    return stock.get(key, default) if stock else default

def safe_name(stock):
    return stock.get("name", "Unbekannt") if stock else "Unbekannt"

def get_top_flop_stocks(data, top_n=5):
    sorted_stocks = sorted(data, key=lambda x: safe_get(x, "prozentuale_veränderung"), reverse=True)
    top = sorted_stocks[:top_n]
    flop = sorted_stocks[-top_n:]
    return top, flop

def get_growth_recommendations(data, n=3):
    sorted_growth = sorted(data, key=lambda x: safe_get(x, "wachstumspotenzial"), reverse=True)
    return sorted_growth[:n]

def generate_ki_fazit(stocks):
    stock_names = ", ".join([safe_name(s) for s in stocks])
    content = f"Schreibe ein kurzes KI-Fazit über die Aktien: {stock_names}."
    
    url = f"https://generativelanguage.googleapis.com/v1beta2/models/{MODEL_NAME}:generateText?key={API_KEY}"
    data = {
        "model": MODEL_NAME,
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

def create_diagram(top, flop):
    names = [safe_name(s) for s in top + flop]
    values = [safe_get(s, "prozentuale_veränderung") for s in top + flop]
    colors = ["green"] * len(top) + ["red"] * len(flop)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, values, color=colors)
    plt.ylabel("Prozentuale Veränderung")
    plt.title("Top & Flop 5 Aktien")
    plt.xticks(rotation=45, ha="right")
    
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f"{val:.2f}%", ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    plt.close()
    return img_buffer

def send_to_discord(top, flop, recommendations, ki_fazit, diagram_bytes):
    def format_table(stocks, is_top=True):
        lines = ["```diff"]
        for s in stocks:
            name = safe_name(s)
            val = safe_get(s, "prozentuale_veränderung")
            emoji = "📈" if val > 0 else "📉"
            sign = "+" if is_top else "-"
            lines.append(f"{sign} {name}: {emoji} {val:.2f}%")
        lines.append("```")
        return "\n".join(lines)
    
    message = "**📈 Top 5 Aktien**\n" + format_table(top, is_top=True)
    message += "\n**📉 Flop 5 Aktien**\n" + format_table(flop, is_top=False)
    message += "\n**💡 Empfehlungen (höchstes Wachstumspotenzial)**\n"
    message += ", ".join([safe_name(s) for s in recommendations])
    message += f"\n\n**🤖 KI-Fazit**\n{ki_fazit}"
    
    # Nachricht senden
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Senden der Nachricht an Discord: {e}")
    
    # Diagramm senden
    try:
        files = {"file": ("diagram.png", diagram_bytes, "image/png")}
        r = requests.post(DISCORD_WEBHOOK_URL, files=files)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Senden des Diagramms an Discord: {e}")

# === MAIN ===
if __name__ == "__main__":
    data = load_data(MONITOR_OUTPUT_FILE)
    top, flop = get_top_flop_stocks(data)
    recommendations = get_growth_recommendations(data)
    ki_fazit = generate_ki_fazit(recommendations)
    diagram_bytes = create_diagram(top, flop)
    send_to_discord(top, flop, recommendations, ki_fazit, diagram_bytes)
