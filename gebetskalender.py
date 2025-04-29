import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}

# Bekannte korrekte Gebetszeiten für den 29. April 2025
# Format: Name: (Stunde, Minute) in 24h-Format für deutsche Zeit
KORREKTE_ZEITEN = {
    "Fajr": (4, 15),
    "Zuhr": (13, 20),
    "Asr": (17, 19),
    "Maghrib": (20, 46),
    "Isha": (21, 53)
}

# === ICS-Datei manuell erstellen - OHNE Zeitzonenangaben
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
print("Direkte Erstellung von Gebetszeiten für Google Calendar:")
print("-----------------------------------------------------")

# === Ereignisse erstellen - mit FLOATING TIMES (keine Zeitzonenangabe)
for name, (hour, minute) in KORREKTE_ZEITEN.items():
    if name not in pflichtgebete:
        continue

    # Aktuelles Datum nehmen
    now = datetime.now()
    event_date = now.strftime("%Y%m%d")

    # Zeiten direkt formatieren ohne Zeitzonenangabe
    # Das Format ist YYYYMMDDTHHMMSS - ohne Z am Ende (wichtig!)
    dtstart = f"{event_date}T{hour:02d}{minute:02d}00"

    # Zehn Minuten später für Ende
    end_time = datetime(now.year, now.month, now.day, hour, minute) + timedelta(minutes=10)
    dtend = f"{event_date}T{end_time.hour:02d}{end_time.minute:02d}00"

    print(f"{name}: {hour:02d}:{minute:02d} Uhr")

    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{name} Gebet",
        f"DTSTART:{dtstart}",  # Keine Zeitzone = floating time
        f"DTEND:{dtend}",  # Keine Zeitzone = floating time
        f"DESCRIPTION:{name} Gebetszeit {hour:02d}:{minute:02d} Uhr",
        "END:VEVENT"
    ]
    ics_content.extend(event_lines)

# Ende der Kalenderdatei
ics_content.append("END:VCALENDAR")

# === ICS-Datei speichern
with open("gebetszeiten_direktezeit.ics", "w") as f:
    f.write("\r\n".join(ics_content))

print("\n✅ gebetszeiten_direktezeit.ics erfolgreich erstellt!")
print("WICHTIG: Diese Version verwendet 'Floating Times' ohne Zeitzonenangabe.")
print("Die Zeiten werden exakt so interpretiert, wie sie eingegeben wurden,")
print("unabhängig von der Zeitzone des Kalenders.")