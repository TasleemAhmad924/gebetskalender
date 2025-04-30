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

# === Heute scrapen
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)

# Verwende dynamisch immer den heutigen Tag
prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]

# === ICS-Inhalt mit korrekter Zeitzonendefinition
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VTIMEZONE",
    "TZID:Europe/Berlin",
    "BEGIN:STANDARD",
    "DTSTART:20241027T030000",
    "TZOFFSETFROM:+0200",
    "TZOFFSETTO:+0100",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "END:STANDARD",
    "BEGIN:DAYLIGHT",
    "DTSTART:20250330T020000",
    "TZOFFSETFROM:+0100",
    "TZOFFSETTO:+0200",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "END:DAYLIGHT",
    "END:VTIMEZONE"
]

print("Gebetszeiten für Google Calendar (in Berlin-Zeitzone):")
print("-----------------------------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    # Zeitpunkt in Berlin-Zeit
    timestamp_ms = prayer["time"]
    dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # Formatierung mit Zeitzonen-ID
    dtstart = dt_berlin.strftime("%Y%m%dT%H%M%S")
    dtend = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr (Berlin-Zeit)")

    ics_content.extend([
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART;TZID=Europe/Berlin:{dtstart}",
        f"DTEND;TZID=Europe/Berlin:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ])

ics_content.append("END:VCALENDAR")

# === Datei speichern
with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt – Mit korrekter TZID=Europe/Berlin")