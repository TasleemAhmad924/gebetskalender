import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}
berlin_tz = pytz.timezone("Europe/Berlin")

# === Heute scrapen (wie gehabt) ===
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)

prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]

# === ICS-Inhalt vorbereiten (MIT Zeitzone) ===
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
]

print("Gebetszeiten für Google Calendar (mit expliziter Zeitzone):")
print("----------------------------------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    # Zeitpunkt in Berlin-Zeit (wie gehabt)
    timestamp_ms = prayer["time"]
    dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # *** WICHTIG: KEINE UTC-Konvertierung ***
    dtstart = dt_berlin.strftime("%Y%m%dT%H%M%S")
    dtend = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

    ics_content.extend([
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART;TZID=Europe/Berlin:{dtstart}",  # Zeitzone hinzugefügt
        f"DTEND;TZID=Europe/Berlin:{dtend}",    # Zeitzone hinzugefügt
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ])

ics_content.append("END:VCALENDAR")

# === Datei speichern (wie gehabt) ===
with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt – mit expliziter Zeitzone.")