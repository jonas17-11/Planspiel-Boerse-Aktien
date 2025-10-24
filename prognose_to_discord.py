import os
import io
import requests
import matplotlib.pyplot as plt
from analyzer import get_analysis

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")

# 🔹 Chart zeichnen
def plot_chart(df, title):
    plt.figure(figsize=(6,3))
    plt.plot(df.index, df['Close'], label="Kurs", color="blue")
    plt.plot(df.index, df['Close'].rolling(10).mean(), label="Trendlinie", color="orange", linestyle="--")
    plt.title(title, fontsize=10)
    plt.xlabel("Datum", fontsize=7)
    plt.ylabel("Preis", fontsize=7)
    plt.xticks(rotation=45, fontsize=6)
    plt.yticks(fontsize=6)
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
        print("❌ Keine Ergebnisse.")
        return

    top_up = sorted(analysis, key=lambda x: x["change"], reverse=True)[:10]
    top_down = sorted(analysis, key=lambda x: x["change"])[:10]

    embed = {
        "username": "📊 Markt-Prognose",
        "embeds": [{
            "title": "🌍 Marktanalyse – Top Bewegungen",
            "description": (
                "**📈 Top 10 Aufsteiger:**\n" +
                "\n".join([f"**{a['name']}** ({a['ticker']}) → +{a['change']:.2f}%\n_{a['pattern']}_" for a in top_up]) +
                "\n\n**📉 Top 10 Absteiger:**\n" +
                "\n".join([f"**{a['name']}** ({a['ticker']}) → {a['change']:.2f}%\n_{a['pattern']}_" for a in top_down])
            ),
            "color": 0x2ECC71
        }]
    }

    files = []
    for asset in top_up[:3] + top_down[:3]:
        buf = plot_chart(asset['df'], f"{asset['name']} ({asset['pattern']})")
        files.append(("file", (f"{asset['ticker']}.png", buf, "image/png")))

    response = requests.post(WEBHOOK_URL, data={"payload_json": str(embed)}, files=files)
    if response.status_code in (200, 204):
        print("✅ Prognose erfolgreich an Discord gesendet!")
    else:
        print(f"❌ Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
