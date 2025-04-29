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
source_tz = pytz.timezone("Europe/London")  # Die Website nutzt UK-Zeitzone (AM/PM)
target_tz = pytz.timezone("Europe/Berlin")  # Lokale Zielzeit
calendar = Calendar()

# === Ereignisse erstellen
for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    timestamp_ms = prayer["time"]

    # Erst in UK-Zeit konvertieren (wie auf der Website)
    dt_uk = datetime.fromtimestamp(timestamp_ms / 1000, source_tz)

    # Dann in deutsche Zeit umwandeln
    dt_berlin = dt_uk.astimezone(target_tz)

    # Wichtig: Den Zeitstempel als naive Zeit speichern, aber im Format
    # der Berliner Zeit (die ics-Bibliothek kümmert sich um die UTC-Konvertierung)
    dt_naive = dt_berlin.replace(tzinfo=None)

    event = Event()
    event.name = f"{name} Gebet"
    event.begin = dt_naive
    event.end = dt_naive + timedelta(minutes=10)

    # Explizit die Zeitzone für das Event setzen
    event.begin = event.begin.replace(tzinfo=target_tz)
    event.end = event.end.replace(tzinfo=target_tz)

    event.description = f"{name} Gebetszeit automatisch aus alislam.org"
    calendar.events.add(event)

# === ICS-Datei speichern
with open("gebetszeiten.ics", "w") as f:
    f.writelines(calendar)

print("✅ gebetszeiten.ics erfolgreich erstellt!")