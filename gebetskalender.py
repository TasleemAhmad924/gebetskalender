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

# === ICS-Inhalt vorbereiten (ohne Zeitzone, mit korrekter Uhrzeit als UTC)
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
]

print("Gebetszeiten für Google Calendar (als UTC exportiert, aber Berlin-Zeiten):")
print("--------------------------------------------------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    # Zeitpunkt in Berlin-Zeit
    timestamp_ms = prayer["time"]
    dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # Absichtlich als UTC exportieren, damit Google es exakt so rendert
    dt_fake_utc = dt_berlin.astimezone(pytz.UTC)
    dtstart = dt_fake_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend = (dt_fake_utc + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%SZ")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr → gespeichert als UTC {dt_fake_utc.strftime('%H:%M')}")

    ics_content.extend([
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ])

ics_content.append("END:VCALENDAR")

# === Datei speichern
with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt – Google Calendar zeigt Berliner Uhrzeit korrekt an.")
