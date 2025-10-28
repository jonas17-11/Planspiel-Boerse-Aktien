import os
import io
import matplotlib.pyplot as plt
import requests
from analyzer import analyze_and_predict_all

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")  # Discord Webhook
TOP_N = 5  # Anzahl Top Assets pro Richtung

# --- Pattern-Erklärungen ---
PATTERN_EXPLANATIONS = {
    "Bullish Engulfing": "Starkes Kaufsignal, letzte Kerze überdeckt die vorherige Abwärtskerze.",
    "Bearish Engulfing": "Starkes Verkaufssignal, letzte Kerze überdeckt die vorherige Aufwärtskerze.",
    "Hammer": "Möglicher Trendwechsel nach unten, langer Schatten nach unten.",
    "Inverted Hammer": "Möglicher Trendwechsel nach unten, langer Schatten nach oben.",
    "Doji": "Unentschlossenheit am Markt, Trend unklar.",
    "Morning Star": "Bullishes Umkehrmuster, Signal für Aufwärtsbewegung.",
    "Evening Star": "Bärisches Umkehrmuster, Signal für Abwärtsbewegung.",
    "Hanging Man": "Bärisches Signal nach Aufwärtstrend.",
    "Shooting Star": "Bärisches Signal nach Aufwärtstrend."
}

# --- Diagramm erstellen ---
def plot_asset(df, forecast_df, name, trend_up=True):
    plt.figure(figsize=(8, 4))
    plt.plot(df.index, df['Close'], label='Aktueller Kurs', color='blue')
    if forecast_df is not None:
        plt.plot(forecast_df.index, forecast_df['Predicted'],
                 label='Prognose', color='green' if trend_up else 'red', linestyle='--')
    plt.title(f"{name} - Trend: {'Aufwärts' if trend_up else 'Abwärts'}")
    plt.xlabel("Datum")
    plt.ylabel("Preis")
    plt.legend()
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf

# --- Discord-Nachricht bauen ---
def build_discord_message(top_up, top_down):
    message = ""
    # Aufwärts
    if top_up:
        message += "**📈 Top Aufwärts-Trends:**\n"
        for a in top_up[:TOP_N]:
            explanation = PATTERN_EXPLANATIONS.get(a['pattern'], "")
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n  *{explanation}*\n"
        message += "\n"
    # Abwärts
    if top_down:
        message += "**📉 Top Abwärts-Trends:**\n"
        for a in top_down[:TOP_N]:
            explanation = PATTERN_EXPLANATIONS.get(a['pattern'], "")
            message += f"- **{a['name']}**: {a['pattern']} ({a['confidence']}%)\n  *{explanation}*\n"
    return message

# --- Nachricht posten ---
def post_to_discord():
    top_up, top_down = analyze_and_predict_all()
    if not top_up and not top_down:
        print("Keine aussagekräftigen Trends gefunden.")
        return

    message = build_discord_message(top_up, top_down)

    files = []
    for a in top_up[:TOP_N] + top_down[:TOP_N]:
        # forecast_df kann None sein, daher prüfen
        forecast_df = a.get('forecast_df', None)
        buf = plot_asset(a['df'], forecast_df, a['name'], trend_up=(a['trend']=="up"))
        files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, data=payload, files=files)
    if response.status_code in (200, 204):
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
