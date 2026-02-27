"""
Calendar generator — converts parsed shift data into a .ics file.

The .ics file can be imported into Google Calendar via:
  Settings → Import & Export → Import
"""

import uuid
from datetime import datetime, timezone, date, time
from pathlib import Path

from icalendar import Calendar, Event

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Set your local timezone offset (e.g. "Europe/London", "America/New_York")
# or use a UTC offset string like "+01:00"
TIMEZONE = "Australia/Sydney"

# Name shown for each calendar event
EVENT_SUMMARY = "Work Shift"

# Event colour — hex value of Google Calendar's "Flamingo" (#E67C73)
# Recognised by Apple Calendar and some Google Calendar versions on import.
EVENT_COLOR = "#E67C73"

# Where to save the output file (relative to project root)
OUTPUT_DIR = Path(".")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_ics(shifts: list[dict], output_path: Path | None = None) -> Path:
    """
    Generate a .ics file from a list of shift dicts.

    Each shift dict must have:
        date  (datetime.date)
        start (datetime.time)
        end   (datetime.time)
        title (str)

    Returns the path to the created .ics file.
    """
    if not shifts:
        raise ValueError("No shifts to write — the parser returned an empty list.")

    cal = Calendar()
    cal.add("prodid", "-//emailToCalendar//emailToCalendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "Work Shifts")
    cal.add("x-wr-timezone", TIMEZONE)

    for shift in shifts:
        event = _make_event(shift)
        cal.add_component(event)

    if output_path is None:
        earliest = min(s["date"] for s in shifts)
        output_path = OUTPUT_DIR / f"shifts_{earliest.isoformat()}.ics"

    output_path.write_bytes(cal.to_ical())
    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_event(shift: dict) -> Event:
    """Build a VEVENT component from a single shift dict."""
    event = Event()

    shift_date: date = shift["date"]
    start: time = shift["start"]
    end: time = shift["end"]
    title: str = shift.get("title", EVENT_SUMMARY)

    # Use floating (local) datetimes — Google Calendar respects these with
    # your account's timezone setting
    dt_start = datetime.combine(shift_date, start)
    dt_end = datetime.combine(shift_date, end)

    # Handle overnight shifts (end before start)
    if dt_end <= dt_start:
        from datetime import timedelta
        dt_end += timedelta(days=1)

    event.add("summary", title)
    event.add("dtstart", dt_start)
    event.add("dtend", dt_end)
    event.add("dtstamp", datetime.now(tz=timezone.utc))
    event.add("uid", str(uuid.uuid4()))
    event.add("color", EVENT_COLOR)

    return event
