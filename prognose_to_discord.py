import os
import requests
from analyzer import get_analysis
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image
import imgkit  # Zum Rendern von HTML zu Bild (alternativ selenium, hier als Beispiel)

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")
CHART_DIR = "charts_html"
IMG_DIR = "charts_img"

os.makedirs(CHART_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def save_chart(item):
    df = item['df']
    forecast = item['forecast']

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines+markers',
        name='Aktueller Kurs',
        line=dict(color='green' if item['confidence'] > 0 else 'red')
    ))
    if forecast is not None and not forecast.empty:
        fig.add_trace(go.Scatter(
            x=forecast.index, y=forecast['Predicted'],
            mode='lines+markers',
            name='Prognose',
            line=dict(color='red', dash='dash')
        ))

    fig.update_layout(
        title=f"{item['name']} - {item['pattern']}",
        xaxis_title='Datum',
        yaxis_title='Preis',
        template='plotly_dark'
    )

    # Speichern als interaktive HTML-Datei
    html_path = os.path.join(CHART_DIR, f"{item['ticker']}.html")
    fig.write_html(html_path)

    # Speichern als PNG für Discord
    img_path = os.path.join(IMG_DIR, f"{item['ticker']}.png")
    pio.write_image(fig, img_path, format='png', scale=2)
    return img_path, html_path

def build_discord_message(top, flop):
    message = "**📈 Top 10 steigende Assets:**\n```diff\n"
    for item in top:
        message += f"+ {item['name']}: {item['pattern']} ({item['confidence']}%)\n"
    message += "```\n\n"

    message += "**📉 Top 10 fallende Assets:**\n```diff\n"
    for item in flop:
        message += f"- {item['name']}: {item['pattern']} ({item['confidence']}%)\n"
    message += "```\n"

    message += "\n💹 Interaktive Charts (Hover für Details) sind lokal gespeichert oder können gehostet werden."
    return message

def post_to_discord():
    top, flop = get_analysis()
    if not top and not flop:
        print("Keine Analyse-Ergebnisse.")
        return

    message = build_discord_message(top, flop)

    files = []
    for item in top + flop:
        img_path, html_path = save_chart(item)
        files.append(('file', (os.path.basename(img_path), open(img_path, 'rb'), 'image/png')))

    response = requests.post(WEBHOOK_URL, data={"content": message}, files=files)
    if response.status_code in [200, 204]:
        print("Erfolgreich in Discord gesendet ✅")
    else:
        print(f"Fehler beim Senden: {response.status_code} {response.text}")

if __name__ == "__main__":
    post_to_discord()
