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

# === Aktuelles Datum in Berlin-Zeit ===
today_berlin = datetime.now(berlin_tz).date()

# === Gebetszeiten von der Website holen ===
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)

# Alle verfügbaren Tage in multiDayTimings prüfen
multi_day_timings = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"]

# Den Eintrag für den aktuellen Tag finden
prayers = None
for timing in multi_day_timings:
    timestamp_ms = timing["prayers"][0]["time"]
    date = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz).date()
    if date == today_berlin:
        prayers = timing["prayers"]
        break

if not prayers:
    raise Exception(f"Keine Gebetszeiten für {today_berlin} gefunden!")

# === ICS-Inhalt vorbereiten ===
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    # VTIMEZONE für Europe/Berlin
    "BEGIN:VTIMEZONE",
    "TZID:Europe/Berlin",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:+0200",
    "TZOFFSETTO:+0100",
    "TZNAME:CET",
    "DTSTART:19701025T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "END:STANDARD",
    "BEGIN:DAYLIGHT",
    "TZOFFSETFROM:+0100",
    "TZOFFSETTO:+0200",
    "TZNAME:CEST",
    "DTSTART:19700329T020000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "END:DAYLIGHT",
    "END:VTIMEZONE"
]

print(f"Gebetszeiten für {today_berlin} (Europe/Berlin):")
print("------------------------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    # Zeitpunkt in Berlin-Zeit
    timestamp_ms = prayer["time"]
    dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # Format für DTSTART/DTEND mit TZID
    dtstart = dt_berlin.strftime("%Y%m%dT%H%M%S")
    dtend = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

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

# === Datei speichern ===
with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt – kompatibel mit Google Calendar.")