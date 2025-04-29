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
    print("🌐 Lade Gebetszeiten von alislam.org...")
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
        # Zwei verschiedene Methoden zur Datumsformatierung testen

        # METHODE 1: Absolutes UTC-Format mit "Z" am Ende
        # Konvertiere Berlin Zeit zurück zu UTC für Kalenderkompatibilität
        dt_utc = dt_berlin.astimezone(pytz.UTC)
        dtstart_utc = dt_utc.strftime("%Y%m%dT%H%M%SZ")
        dtend_utc = (dt_utc + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%SZ")

        # Event für Methode 1
        event_utc = [
            "BEGIN:VEVENT",
            f"UID:{name}-UTC-{today_date}@gebetskalender",
            f"SUMMARY:{name} Gebet (UTC)",
            f"DTSTART:{dtstart_utc}",
            f"DTEND:{dtend_utc}",
            f"DESCRIPTION:{name} Gebetszeit für {today_date} - Dargestellt in UTC-Format",
            "END:VEVENT"
        ]
        ics_content.extend(event_utc)

        # METHODE 2: Mit expliziter Zeitzone
        dtstart_local = dt_berlin.strftime("%Y%m%dT%H%M%S")
        dtend_local = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")

        # Event für Methode 2
        event_local = [
            "BEGIN:VEVENT",
            f"UID:{name}-TZID-{today_date}@gebetskalender",
            f"SUMMARY:{name} Gebet (TZID)",
            f"DTSTART;TZID={TIMEZONE}:{dtstart_local}",
            f"DTEND;TZID={TIMEZONE}:{dtend_local}",
            f"DESCRIPTION:{name} Gebetszeit für {today_date} - Mit expliziter Zeitzone",
            "END:VEVENT"
        ]
        ics_content.extend(event_local)

        # METHODE 3: Direkter Wert in lokaler Zeit mit symbolischem Offset
        # Hinweis: Dieses Format kann robuster für einige Kalenderanwendungen sein
        offset = dt_berlin.strftime("%z")
        offset_formatted = f"{offset[:3]}:{offset[3:]}"  # +0200 zu +02:00 formatieren
        dtstart_offset = dt_berlin.strftime("%Y%m%dT%H%M%S") + offset_formatted
        dtend_offset = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S") + offset_formatted

        # Event für Methode 3
        event_offset = [
            "BEGIN:VEVENT",
            f"UID:{name}-OFFSET-{today_date}@gebetskalender",
            f"SUMMARY:{name} Gebet (Offset)",
            f"DTSTART:{dtstart_offset}",
            f"DTEND:{dtend_offset}",
            f"DESCRIPTION:{name} Gebetszeit für {today_date} - Mit direktem Zeitzonenoffset",
            "END:VEVENT"
        ]
        ics_content.extend(event_offset)

    ics_content.append("END:VCALENDAR")

    # Datei speichern
    with open("gebetszeiten.ics", "w") as f:
        f.write("\r\n".join(ics_content))

    # Zur Diagnose auch eine Textausgabe der Datei erstellen
    with open("gebetszeiten_debug.txt", "w") as f:
        f.write("\r\n".join(ics_content))

    return ics_content


def main():
    try:
        prayer_times = get_prayer_times()

        print("\nGebetszeiten für heute (Berlin):")
        print("--------------------------------")
        for name, dt_berlin in prayer_times.items():
            print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

        print("\n📅 Erstelle ICS-Datei mit drei verschiedenen Methoden...")
        create_ics_file(prayer_times)

        print("\n✅ gebetszeiten.ics erfolgreich erstellt.")
        print("   Diese Datei enthält jedes Gebet in drei verschiedenen Formaten.")
        print("   Bitte teste und finde heraus, welches in deinem Kalender richtig angezeigt wird.")
        print("\n📝 Zusätzlich wurde eine gebetszeiten_debug.txt erstellt, die identisch")
        print("   mit der ICS-Datei ist, aber leichter zu lesen ist.")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()