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
heute = datetime.now(berlin_tz).date()

# === Heute scrapen
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)

# === Gebetszeiten für HEUTE suchen
multi_day = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"]
heutige_gebete = None

for tag in multi_day:
    date_str = tag["date"]  # z. B. "2025-04-30"
    datum = datetime.fromtimestamp(date_str / 1000, berlin_tz).date()
    if datum == heute:
        heutige_gebete = tag["prayers"]
        break

if heutige_gebete is None:
    raise Exception("Keine Gebetszeiten für heute gefunden!")

# === ICS-Inhalt vorbereiten
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
]

print("Gebetszeiten für Google Calendar (feste Lokalzeit via UTC):")
print("-----------------------------------------------------------")

for prayer in heutige_gebete:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp_ms = prayer["time"]
    dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # Absichtlich als UTC abspeichern, aber lokale Zeit behalten
    dt_fake_utc = dt_berlin.astimezone(pytz.UTC)
    dtstart = dt_fake_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend = (dt_fake_utc + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%SZ")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr → gespeichert als UTC {dt_fake_utc.strftime('%H:%M')}")

    event = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ]
    ics_content.extend(event)

ics_content.append("END:VCALENDAR")

# === Datei speichern
with open("gebetszeiten.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten.ics erfolgreich erstellt – Google Calendar zeigt Berliner Uhrzeit korrekt an.")
