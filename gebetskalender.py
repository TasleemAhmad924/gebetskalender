import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid
from zoneinfo import ZoneInfo  # Moderne Alternative zu pytz

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}
TIMEZONE = "Europe/Berlin"
berlin_tz = ZoneInfo(TIMEZONE)

# === Heute scrapen
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)
prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]

# === Datum heute für VTIMEZONE-Block
heute = datetime.now(berlin_tz)
jahr = heute.year

# === ICS-Inhalt vorbereiten
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    f"X-WR-CALNAME:Islamische Gebetszeiten",
    f"X-WR-TIMEZONE:{TIMEZONE}",
]

# VTIMEZONE-Block für Europe/Berlin hinzufügen
# Dies ist wichtig für die korrekte Interpretation der Zeitzonen
ics_content.extend([
    "BEGIN:VTIMEZONE",
    f"TZID:{TIMEZONE}",
    "BEGIN:DAYLIGHT",
    f"TZOFFSETFROM:+0100",
    f"TZOFFSETTO:+0200",
    f"TZNAME:CEST",
    f"DTSTART:{jahr}0330T020000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "END:DAYLIGHT",
    "BEGIN:STANDARD",
    f"TZOFFSETFROM:+0200",
    f"TZOFFSETTO:+0100",
    f"TZNAME:CET",
    f"DTSTART:{jahr}1030T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "END:STANDARD",
    "END:VTIMEZONE"
])

print("Gebetszeiten für Kalender (mit korrekter Zeitzone):")
print("---------------------------------------------------")

today_date = datetime.now(berlin_tz).strftime("%Y-%m-%d")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp_ms = prayer["time"]
    # Zeit von Millisekunden in Sekunden umrechnen und in Berlin-Zeitzone anzeigen
    dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # Format mit expliziter TZID - kein "Z" am Ende
    dtstart = dt_berlin.strftime("%Y%m%dT%H%M%S")
    dtend = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr Berlin Zeit")

    event = [
        "BEGIN:VEVENT",
        f"UID:{name}-{today_date}@gebetskalender",
        f"SUMMARY:{name} Gebet",
        f"DTSTART;TZID={TIMEZONE}:{dtstart}",
        f"DTEND;TZID={TIMEZONE}:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit für {today_date}",
        "END:VEVENT"
    ]
    ics_content.extend(event)

ics_content.append("END:VCALENDAR")

# === Datei speichern
with open("gebetszeiten.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten.ics erfolgreich erstellt mit korrekter VTIMEZONE-Definition.")