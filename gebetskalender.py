import requests
from datetime import datetime, timedelta
import pytz
import json
import re
import uuid

# === Einstellungen ===
URL = "https://www.alislam.org/adhan"
pflichtgebete = {"Fajr", "Zuhr", "Asr", "Maghrib", "Isha"}
TIMEZONE = "Europe/Berlin"
berlin_tz = pytz.timezone(TIMEZONE)


def get_prayer_times():
    """Lädt und analysiert die Gebetszeiten"""
    response = requests.get(URL)
    html = response.text

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
    if not match:
        raise Exception("Keine Gebetszeiten gefunden!")

    json_str = match.group(1)
    data = json.loads(json_str)

    # Die Gebetszeiten befinden sich hier
    prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]

    # Die API liefert UTC-Timestamps in Millisekunden
    prayer_times = {}
    for prayer in prayers:
        name = prayer["name"]
        if name in pflichtgebete:
            # Konvertiere Millisekunden in Sekunden und von UTC in lokale Zeit
            timestamp_ms = prayer["time"]
            dt_utc = datetime.fromtimestamp(timestamp_ms / 1000, pytz.UTC)
            dt_berlin = dt_utc.astimezone(berlin_tz)
            prayer_times[name] = dt_berlin

    return prayer_times


def create_ics_file(prayer_times):
    """Erstellt eine .ics-Datei mit den Gebetszeiten"""
    heute = datetime.now(berlin_tz)
    jahr = heute.year
    today_date = heute.strftime("%Y-%m-%d")

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

    # Gebetszeiten als Events hinzufügen
    for name, dt_berlin in prayer_times.items():
        # Format mit expliziter TZID - kein "Z" am Ende
        dtstart = dt_berlin.strftime("%Y%m%dT%H%M%S")
        dtend = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

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

    # Datei speichern
    with open("gebetszeiten.ics", "w") as f:
        f.write("\r\n".join(ics_content))

    return ics_content


def main():
    print("⏱️ Lade Gebetszeiten...")
    prayer_times = get_prayer_times()

    print("\nGebetszeiten für heute (Berlin):")
    print("--------------------------------")
    for name, dt_berlin in prayer_times.items():
        print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

    print("\n📅 Erstelle ICS-Datei...")
    create_ics_file(prayer_times)

    print("\n✅ gebetszeiten.ics erfolgreich erstellt mit korrekter VTIMEZONE-Definition.")


if __name__ == "__main__":
    main()