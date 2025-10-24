import os
import io
import requests
import matplotlib.pyplot as plt
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

# --- Chart zeichnen ---
def plot_prediction(df, forecast, title):
    plt.figure(figsize=(6,3))
    plt.plot(df.index, df["Close"], color="blue", label="Realer Kurs")
    if forecast is not None:
        plt.plot(forecast.index, forecast["Predicted"], color="red", linestyle="--", label="Prognose")
    plt.title(title, fontsize=10)
    plt.xlabel("Datum", fontsize=7)
    plt.ylabel("Preis", fontsize=7)
    plt.legend(fontsize=6)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    plt.close()
    return buf

def post_to_discord():
    analysis = get_analysis()
    if not analysis:
        print("Keine Analyseergebnisse.")
        return

    top_up = sorted([a for a in analysis if a["predicted_change"] > 0],
                    key=lambda x: x["predicted_change"], reverse=True)[:10]
    top_down = sorted([a for a in analysis if a["predicted_change"] < 0],
                      key=lambda x: x["predicted_change"])[:10]

    def send_section(title, assets):
        content = f"**{title}**\n\n"
        for a in assets:
            content += f"**{a['name']}** ({a['ticker']})\n"
            content += f"{a['pattern']} ({a['confidence']}%)\n"
            content += f"📈 Prognose: {'+' if a['predicted_change']>0 else ''}{a['predicted_change']:.2f}%\n\n"

        files = []
        for a in assets:
            buf = plot_prediction(a["df"], a["forecast"], f"{a['name']} ({a['pattern']})")
            files.append(("file", (f"{a['ticker']}.png", buf, "image/png")))

        response = requests.post(WEBHOOK_URL, data={"content": content}, files=files)
        if response.status_code in (200, 204):
            print(f"✅ {title} erfolgreich gesendet.")
        else:
            print(f"❌ Fehler: {response.status_code} {response.text}")

    send_section("📈 **Top 10 – Wahrscheinliche Aufsteiger**", top_up)
    send_section("📉 **Top 10 – Wahrscheinliche Absteiger**", top_down)

if __name__ == "__main__":
    post_to_discord()
