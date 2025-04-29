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


def get_last_sunday(year, month):
    """Berechnet das Datum des letzten Sonntags eines Monats."""
    if month == 12:
        last_day = datetime(year, 12, 31)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    while last_day.weekday() != 6:  # 6 = Sonntag
        last_day -= timedelta(days=1)
    return last_day


def get_prayer_times():
    """Lädt und analysiert die Gebetszeiten"""
    response = requests.get(URL)
    html = response.text

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
    if not match:
        raise Exception("Keine Gebetszeiten gefunden!")

    json_str = match.group(1)
    data = json.loads(json_str)

    prayers = data["props"]["pageProps"]["defaultSalatInfo"]["multiDayTimings"][0]["prayers"]

    prayer_times = {}
    for prayer in prayers:
        name = prayer["name"]
        if name in pflichtgebete:
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

    sommerzeit_start = get_last_sunday(jahr, 3).strftime("%Y%m%dT020000")
    winterzeit_start = get_last_sunday(jahr, 10).strftime("%Y%m%dT030000")

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Gebetszeiten//alislam.org//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Islamische Gebetszeiten",
        f"X-WR-TIMEZONE:{TIMEZONE}",
        "BEGIN:VTIMEZONE",
        f"TZID:{TIMEZONE}",
        "X-LIC-LOCATION:Europe/Berlin",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:+0100",
        "TZOFFSETTO:+0200",
        "TZNAME:CEST",
        f"DTSTART:{sommerzeit_start}",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0200",
        "TZOFFSETTO:+0100",
        "TZNAME:CET",
        f"DTSTART:{winterzeit_start}",
        "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
        "END:STANDARD",
        "END:VTIMEZONE"
    ]

    for name, dt_berlin in prayer_times.items():
        dtstart = dt_berlin.strftime("%Y%m%dT%H%M%S")
        dtend = (dt_berlin + timedelta(minutes=10)).strftime("%Y%m%dT%H%M%S")
        uid = f"{name.lower()}-{dt_berlin.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}@gebetskalender"

        event = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"SUMMARY:{name} Gebet",
            f"DTSTART;TZID={TIMEZONE}:{dtstart}",
            f"DTEND;TZID={TIMEZONE}:{dtend}",
            f"DESCRIPTION:{name} Gebetszeit für {dt_berlin.strftime('%Y-%m-%d')}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "END:VEVENT"
        ]
        ics_content.extend(event)

    ics_content.append("END:VCALENDAR")

    with open("gebetszeiten.ics", "w", encoding="utf-8") as f:
        f.write("\r\n".join(ics_content))

    return ics_content


def main():
    print("⏱️ Lade Gebetszeiten...")
    prayer_times = get_prayer_times()

    print("\nGebetszeiten für heute (Berlin):")
    print("--------------------------------")
    for name, dt_berlin in sorted(prayer_times.items(), key=lambda x: x[1]):
        print(f"{name}: {dt_berlin.strftime('%H:%M')} Uhr")

    print("\n📅 Erstelle ICS-Datei...")
    create_ics_file(prayer_times)

    print("\n✅ gebetszeiten.ics erfolgreich erstellt mit vollständigem VTIMEZONE.")


if __name__ == "__main__":
    main()
