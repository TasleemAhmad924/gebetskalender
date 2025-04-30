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

# === Daten holen ===
response = requests.get(URL)
html = response.text

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Gebetszeiten gefunden!")

json_str = match.group(1)
data = json.loads(json_str)

# === Heutige Gebetszeiten extrahieren ===
heute = datetime.now(berlin_tz).date()
alle_tage = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"]

for tag in alle_tage:
    tag_datum = datetime.fromtimestamp(tag["date"] / 1000, berlin_tz).date()
    if tag_datum == heute:
        prayers = tag["prayers"]
        break
else:
    raise Exception("Keine Gebetszeiten für heute gefunden!")

# === ICS generieren ===
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
]

print(f"Gebetszeiten für {heute.strftime('%d.%m.%Y')} (Berliner Zeit):")
print("--------------------------------------------------")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    # Originalzeit aus den Daten (bereits Berliner Zeit)
    dt_berlin = datetime.fromtimestamp(prayer["time"] / 1000, berlin_tz)

    # Als UTC formatieren (aber mit korrekter Berliner Uhrzeit)
    dt_utc = dt_berlin.astimezone(pytz.UTC)
    dtstart = dt_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend = (dt_utc + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%SZ")

    print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr (als UTC: {dt_utc.strftime('%Y-%m-%d %H:%M:%S')})")

    ics_content.extend([
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit (Berlin: {dt_berlin.strftime('%H:%M')})",
        "END:VEVENT"
    ])

ics_content.append("END:VCALENDAR")

# === Datei speichern ===
with open("gebetszeiten.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten.ics erfolgreich erstellt. Importieren Sie diese Datei in Google Calendar.")