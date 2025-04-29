import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}

# === ICS-Datei vorbereiten
berlin_tz = pytz.timezone("Europe/Berlin")
today = datetime.now(berlin_tz).date()
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-TIMEZONE:Europe/Berlin",  # Zeitzone für den Kalender setzen
]

# === Gebetszeiten scrapen
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)

prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]

# === Debug-Ausgabe
print("Gebetszeiten für Google Calendar:")
print("--------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp_ms = prayer["time"]

    # Zeit in Europe/Berlin umrechnen
    dt_utc = datetime.utcfromtimestamp(timestamp_ms / 1000).replace(tzinfo=pytz.UTC)
    dt_berlin = dt_utc.astimezone(berlin_tz)

    start_time = dt_berlin.strftime("%Y%m%dT%H%M%S")
    end_time = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART;TZID=Europe/Berlin:{start_time}",  # explizit TZID
        f"DTEND;TZID=Europe/Berlin:{end_time}",  # explizit TZID
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ]
    ics_content.extend(event_lines)

# === Kalenderdatei abschließen
ics_content.append("END:VCALENDAR")

# === Datei speichern
with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt!")
print("Jetzt kompatibel mit Google Calendar und korrekten Zeiten.")
