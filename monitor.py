import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import json
from google.generativeai import client as gclient

# Load tickers
with open("tickers.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]

# Fetch data
data = []
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.history(period="2d")
        if len(info) < 2:
            continue
        prev_close = info['Close'][-2]
        current = info['Close'][-1]
        change_percent = round((current - prev_close)/prev_close*100,2)
        data.append({
            "ticker": ticker,
            "price": round(current,2),
            "previous_close": round(prev_close,2),
            "change_percent": change_percent
        })
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")

df = pd.DataFrame(data)

# Sort Top/Bottom
top5 = df.sort_values(by="change_percent", ascending=False).head(5)
bottom5 = df.sort_values(by="change_percent").head(5)

# Save JSON for workflow
output = {
    "top5": top5.to_dict(orient="records"),
    "bottom5": bottom5.to_dict(orient="records"),
    "timestamp": str(datetime.now())
}
with open("monitor_output.json", "w") as f:
    json.dump(output, f, indent=2)

# Plot Top/Bottom
plt.figure(figsize=(10,5))
plt.bar(top5['ticker'], top5['change_percent'], color='green', label='Top 5')
plt.bar(bottom5['ticker'], bottom5['change_percent'], color='red', label='Bottom 5')
plt.ylabel("Change %")
plt.title("Top 5 / Bottom 5 Aktien der Stunde")
plt.legend()
plt.tight_layout()
plt.savefig("monitor_plot.png")
plt.close()

# Gemini KI
gclient.configure(api_key=os.getenv("GEMINI_API_KEY"))
try:
    prompt = f"Hier sind die Top 5 und Bottom 5 Aktien mit den Prozentveränderungen:\nTop5: {top5.to_dict(orient='records')}\nBottom5: {bottom5.to_dict(orient='records')}\nGib eine kurze Einschätzung, wo ein Investment sinnvoll sein könnte."
    response = gclient.chat.completions.create(
        model="models/mistral-7b-instruct",
        messages=[{"role":"user","content": prompt}],
        temperature=0.7
    )
    ki_text = response.choices[0].message['content']
except Exception as e:
    ki_text = f"⚠️ KI konnte nicht antworten: {e}"

# Save KI Text
output["ki"] = ki_text
with open("monitor_output.json", "w") as f:
    json.dump(output, f, indent=2)
