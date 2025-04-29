import requests
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz
import json
import re

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}

# === Heute scrapen
response = requests.get(URL)
html = response.text

# JSON extrahieren
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if not match:
    raise Exception("Keine Daten gefunden.")

json_str = match.group(1)
data = json.loads(json_str)

prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]
timezone = data["props"]["pageProps"]["defaultSalatInfo"]["locationInfo"]["timezone"]
tz = pytz.timezone(timezone)

# === Kalender erstellen
calendar = Calendar()
calendar.extra.append("X-WR-TIMEZONE:Europe/Berlin")

for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp_ms = prayer["time"]
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz)

    event = Event()
    event.name = f"{name} Gebet"
    event.begin = dt.strftime("%Y-%m-%d %H:%M:%S%z")
    event.end = (dt + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S%z")
    event.description = f"{name} Gebetszeit automatisch aus alislam.org"
    calendar.events.add(event)

# === ICS-Datei speichern
with open("gebetszeiten.ics", "w") as f:
    f.writelines(calendar)

print("✅ gebetszeiten.ics erfolgreich erstellt!")
