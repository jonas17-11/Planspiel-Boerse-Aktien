import requests
from analyzer import run_analysis_patterns
import os

WEBHOOK_URL = os.getenv("PROGNOSE_WEBHOOK")
if not WEBHOOK_URL:
    raise ValueError("❌ PROGNOSE_WEBHOOK Secret nicht gefunden. Bitte in GitHub Secrets setzen.")

def color_pattern(line, trend_strength):
    """Fügt grün für bullish und rot für bearish Patterns hinzu"""
    if trend_strength > 0:
        return f"+ {line}"  # grün
    else:
        return f"- {line}"  # rot

def format_message():
    report = run_analysis_patterns()
    if not report or report.strip() == "":
        return "❌ Keine Assets oder Patterns erkannt. Bitte prüfen Sie die Ticker in prognose.txt oder die Pattern-Erkennung."

    lines = report.split("\n")
    formatted_lines = ["```diff"]
    for line in lines:
        if line.startswith("📈") or line.startswith("📉"):
            formatted_lines.append(f"\n{line}")
        elif ":" in line:
            symbol, rest = line.split(":", 1)
            if "|" in rest:
                patterns, confidence = rest.split("|")
                patterns = patterns.strip()
                confidence = confidence.strip()
                try:
                    trend_strength = float(confidence.split()[0])
                except:
                    trend_strength = 1  # Default, falls Parsing fehlschlägt
                colored_line = color_pattern(f"{symbol.strip()}: {patterns} | 🔮 {confidence}", trend_strength)
                formatted_lines.append(colored_line)
            else:
                formatted_lines.append(f"{symbol.strip()}: {rest.strip()}")
        else:
            formatted_lines.append(line)
    formatted_lines.append("```")
    return "\n".join(formatted_lines)

def post_to_discord():
    message = format_message()

    # Discord limitiert Nachrichten auf 2000 Zeichen → splitten
    chunk_size = 1900
    payloads = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]

    for idx, chunk in enumerate(payloads, start=1):
        r = requests.post(WEBHOOK_URL, json={"content": chunk})
        if r.status_code not in [200, 204]:
            print(f"❌ Fehler beim Senden von Chunk {idx}: {r.status_code} - {r.text}")
        else:
            print(f"✅ Chunk {idx} erfolgreich an Discord gesendet.")

if __name__ == "__main__":
    print("📤 Sende Top-Picks Chart-Pattern Prognose an Discord...")
    post_to_discord()
