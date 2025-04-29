import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid

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
berlin_tz = pytz.timezone("Europe/Berlin")  # Lokale Zielzeit
today = datetime.now(berlin_tz).date()

# === ICS-Datei manuell erstellen
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
]

# === Debugging-Ausgabe
print("Gebetszeiten für heute:")
print("---------------------")

# === Ereignisse erstellen
for prayer in prayers:
    name = prayer["name"]
    if name not in pflichtgebete:
        continue

    # Timestamp direkt aus der API
    timestamp_ms = prayer["time"]

    # Auch extrahieren wir die menschenlesbare Zeit aus der API für die Debugging-Ausgabe
    time_str = prayer.get("timeStr", "")

    # WICHTIG: Die Timestamps sind bereits für die Zeitzone des Benutzers berechnet,
    # die Website zeigt nur das AM/PM-Format britischer Art an.
    # Wir erstellen daher ein lokales Datum für heute mit der korrekten Uhrzeit.

    # Von UNIX-Timestamp zur datetime
    dt = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

    # PM-Korrektur für Nachmittags-/Abendgebete
    # (Für den Fall, dass der Timestamp nicht korrekt die 24-Stunden-Zeit darstellt)
    if name in ["Zuhr", "Asr", "Maghrib", "Isha"] and dt.hour < 12:
        print(
            f"⚠️ {name}: Korrigiere Zeit von {dt.hour}:{dt.minute:02d} auf {dt.hour + 12}:{dt.minute:02d} (PM-Korrektur)")
        dt = dt.replace(hour=dt.hour + 12)

    # Debugging-Ausgabe
    print(f"{name}: {dt.strftime('%H:%M')} ({time_str})")

    # Datum und Uhrzeit formatieren
    dtstart = dt.strftime("%Y%m%dT%H%M%S")
    dtend = (dt + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

    # Zeitzone explizit als "Europe/Berlin" angeben
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART;TZID=Europe/Berlin:{dtstart}",
        f"DTEND;TZID=Europe/Berlin:{dtend}",
        f"DESCRIPTION:{name} Gebetszeit automatisch aus alislam.org",
        "END:VEVENT"
    ]
    ics_content.extend(event_lines)

# Zeitzonendefinition hinzufügen (wichtig für korrekte Interpretation)
tz_lines = [
    "BEGIN:VTIMEZONE",
    "TZID:Europe/Berlin",
    "BEGIN:STANDARD",
    "DTSTART:19701025T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "TZOFFSETFROM:+0200",
    "TZOFFSETTO:+0100",
    "END:STANDARD",
    "BEGIN:DAYLIGHT",
    "DTSTART:19700329T020000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "TZOFFSETFROM:+0100",
    "TZOFFSETTO:+0200",
    "END:DAYLIGHT",
    "END:VTIMEZONE"
]
ics_content.extend(tz_lines)
ics_content.append("END:VCALENDAR")

# === ICS-Datei speichern
with open("gebetszeiten.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten.ics erfolgreich erstellt!")