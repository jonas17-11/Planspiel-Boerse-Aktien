import json
import os
import requests
import matplotlib.pyplot as plt
from io import BytesIO

# === CONFIG aus Secrets ===
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-turbo"
MONITOR_OUTPUT_FILE = "monitor-output.json"

if not DISCORD_WEBHOOK_URL or not API_KEY:
    raise ValueError("Bitte stelle sicher, dass DISCORD_WEBHOOK und GEMINI_API_KEY gesetzt sind!")

# === Funktionen ===

def load_data(file_path):
    """Lade Aktien-Daten aus monitor-output.json"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_top_flop_stocks(data, top_n=5):
    """Berechne Top und Flop Aktien nach prozentualer Veränderung"""
    sorted_stocks = sorted(data, key=lambda x: x["prozentuale_veränderung"], reverse=True)
    top = sorted_stocks[:top_n]
    flop = sorted_stocks[-top_n:]
    return top, flop

def get_growth_recommendations(data, n=3):
    """Wähle Aktien mit höchstem Wachstumspotenzial"""
    sorted_growth = sorted(data, key=lambda x: x.get("wachstumspotenzial", 0), reverse=True)
    return sorted_growth[:n]

def generate_ki_fazit(stocks):
    """Fragt das KI-Fazit für ausgewählte Aktien ab"""
    stock_names = ", ".join([s["name"] for s in stocks])
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
        return result["candidates"][0]["content"]
    except requests.exceptions.RequestException as e:
        return f"⚠️ KI-Fazit konnte nicht abgerufen werden: {e}"
    except (KeyError, IndexError):
        return "⚠️ KI-Fazit konnte nicht abgerufen werden: Ungültige Antwort vom Modell"

def create_diagram(top, flop):
    """Erstellt ein Balkendiagramm der Top/Flop 5 Aktien"""
    names = [s["name"] for s in top + flop]
    values = [s["prozentuale_veränderung"] for s in top + flop]
    colors = ["green"] * len(top) + ["red"] * len(flop)
    
    plt.figure(figsize=(10, 6))
    plt.bar(names, values, color=colors)
    plt.ylabel("Prozentuale Veränderung")
    plt.title("Top & Flop 5 Aktien")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    plt.close()
    return img_buffer

def send_to_discord(top, flop, recommendations, ki_fazit, diagram_bytes):
    """Sendet alles an Discord"""
    
    def format_table(stocks):
        lines = ["| Aktie | Veränderung % |", "|-------|---------------|"]
        for s in stocks:
            lines.append(f"| {s['name']} | {s['prozentuale_veränderung']:.2f} |")
        return "\n".join(lines)
    
    message = "**📈 Top 5 Aktien**\n" + format_table(top)
    message += "\n\n**📉 Flop 5 Aktien**\n" + format_table(flop)
    message += "\n\n**💡 Empfehlungen (höchstes Wachstumspotenzial)**\n"
    message += ", ".join([s["name"] for s in recommendations])
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
