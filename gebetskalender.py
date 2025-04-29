import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid
import os
import sys

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}

# Bekannte korrekte Gebetszeiten (wenn die API-Daten nicht stimmen)
# Format: Name: (Stunde, Minute) in 24h-Format für deutsche Zeit
bekannte_zeiten = {
    "Fajr": (4, 15),
    "Zuhr": (13, 20),
    "Asr": (17, 19),
    "Maghrib": (20, 46),
    "Isha": (21, 53)
}

# === Heute scrapen
try:
    response = requests.get(URL)
    html = response.text

    # JSON extrahieren
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
    if not match:
        raise Exception("Keine Daten gefunden.")

    json_str = match.group(1)
    data = json.loads(json_str)

    prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]
except Exception as e:
    print(f"Fehler beim Scrapen: {e}")
    print("Verwende stattdessen die bekannten Gebetszeiten.")
    prayers = []

# === ICS-Datei manuell erstellen
berlin_tz = pytz.timezone("Europe/Berlin")
today = datetime.now(berlin_tz).date()
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Gebetszeiten//alislam.org//DE",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
]

# === Debugging-Ausgabe
print("Gebetszeiten für Google Calendar:")
print("--------------------------------")

# === Sammle die Gebetszeiten
gebetszeiten = {}

# Versuche zuerst aus den API-Daten zu extrahieren
if prayers:
    for prayer in prayers:
        name = prayer["name"]
        if name not in pflichtgebete:
            continue

        timestamp_ms = prayer["time"]
        dt_berlin = datetime.fromtimestamp(timestamp_ms / 1000, berlin_tz)

        # AM/PM-Problem korrigieren
        if name == "Zuhr" and dt_berlin.hour < 12:
            dt_berlin = dt_berlin.replace(hour=dt_berlin.hour + 12)
        elif name == "Asr" and dt_berlin.hour < 12:
            dt_berlin = dt_berlin.replace(hour=dt_berlin.hour + 12)
        elif name == "Maghrib" and dt_berlin.hour < 12:
            dt_berlin = dt_berlin.replace(hour=dt_berlin.hour + 12)
        elif name == "Isha" and dt_berlin.hour < 12:
            dt_berlin = dt_berlin.replace(hour=dt_berlin.hour + 12)

        gebetszeiten[name] = dt_berlin

# Überprüfe ob die Zeiten plausibel sind, sonst verwende bekannte Zeiten
for name in pflichtgebete:
    if name not in gebetszeiten or not (0 <= gebetszeiten[name].hour < 24):
        # Zeit fehlt oder ungültig, verwende bekannte Zeit
        if name in bekannte_zeiten:
            hour, minute = bekannte_zeiten[name]
            dt = datetime.now(berlin_tz).replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            gebetszeiten[name] = dt
            print(f"{name}: Verwende bekannte Zeit {hour:02d}:{minute:02d}")
    else:
        print(f"{name}: {gebetszeiten[name].strftime('%H:%M')} (aus API)")

# === Ereignisse erstellen - mit UTC-ZEIT für Google Calendar
for name, dt_berlin in gebetszeiten.items():
    # In UTC umwandeln für Google Calendar
    dt_utc = dt_berlin.astimezone(pytz.UTC)

    # Datum und Uhrzeit formatieren für ICS
    # Für Google Calendar: UTC-Zeit ohne TZID
    dtstart = dt_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend = (dt_utc + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%SZ")

    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART:{dtstart}",  # UTC-Zeit für Google Calendar
        f"DTEND:{dtend}",  # UTC-Zeit für Google Calendar
        f"DESCRIPTION:{name} Gebetszeit {dt_berlin.strftime('%H:%M')} Uhr",
        "END:VEVENT"
    ]
    ics_content.extend(event_lines)

# Ende der Kalenderdatei
ics_content.append("END:VCALENDAR")

# === ICS-Datei speichern
with open("gebetszeiten_google.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_google.ics erfolgreich erstellt!")
print("Diese Version sollte speziell mit Google Calendar kompatibel sein.")
print("Tipp: Wenn die Zeiten immer noch falsch sind, überprüfen Sie die")
print("      Zeitzonen-Einstellungen in Ihrem Google Calendar-Konto.")