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

# === ICS-Kopf vorbereiten
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-TIMEZONE:Europe/Berlin"
]

# === Gebetszeiten scrapen
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_data = json.loads(match.group(1))
multi_day = json_data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"]

# === Heutiges Datum in Berlin
today = datetime.now(berlin_tz).date()

# === Richtigen Tages-Eintrag finden
prayers = None
for day in multi_day:
    timestamp = day["date"]
    date_obj = datetime.fromtimestamp(timestamp / 1000, berlin_tz).date()
    if date_obj == today:
        prayers = day["prayers"]
        break

if not prayers:
    raise Exception(f"Keine Gebetszeiten für {today} gefunden.")

# === Debug-Ausgabe
print("Gebetszeiten für Google Calendar:")
print("--------------------------------")

# === Ereignisse hinzufügen
for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp = prayer["time"]
    dt_utc = datetime.utcfromtimestamp(timestamp / 1000).replace(tzinfo=pytz.UTC)
    dt_berlin = dt_utc.astimezone(berlin_tz)

    dt_start = dt_berlin.strftime("%Y%m%dT%H%M%S")
    dt_end = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

    ics_content += [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART;TZID=Europe/Berlin:{dt_start}",
        f"DTEND;TZID=Europe/Berlin:{dt_end}",
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ]

# === Datei abschließen und speichern
ics_content.append("END:VCALENDAR")

with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt – für den heutigen Tag!")
