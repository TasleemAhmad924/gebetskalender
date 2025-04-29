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
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
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
berlin_tz = pytz.timezone("Europe/Berlin")

# === Debug-Ausgabe
print("Gebetszeiten für Google Calendar:")
print("--------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp_ms = prayer["time"]
    dt_utc = datetime.utcfromtimestamp(timestamp_ms / 1000).replace(tzinfo=pytz.UTC)
    dt_berlin = dt_utc.astimezone(berlin_tz)

    # Konvertiere zurück in UTC für Google Calendar
    dtstart = dt_berlin.astimezone(pytz.UTC).strftime("%Y%m%dT%H%M%SZ")
    dtend = (dt_berlin + timedelta(minutes=10)).astimezone(pytz.UTC).strftime("%Y%m%dT%H%M%SZ")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ]
    ics_content.extend(event_lines)

# === Kalenderdatei abschließen
ics_content.append("END:VCALENDAR")

# === Datei speichern
with open("gebetszeiten.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten.ics erfolgreich erstellt!")
print("Funktioniert garantiert mit Google Calendar.")
