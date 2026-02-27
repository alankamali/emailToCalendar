"""
Calendar generator — adds parsed shift data directly to Google Calendar via the API.
"""

from datetime import datetime, date, time, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TIMEZONE = "Australia/Sydney"

# Google Calendar colorId for "Flamingo" (reliably applied via the API)
COLOR_ID = "4"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_to_calendar(service, shifts: list[dict]) -> list[str]:
    """
    Create Google Calendar events for each shift.

    Args:
        service: Google Calendar API service object (from get_calendar_service()).
        shifts:  List of shift dicts with keys: date, start, end, title.

    Returns:
        List of URLs for the created events.
    """
    if not shifts:
        raise ValueError("No shifts to add — the parser returned an empty list.")

    urls = []
    for shift in shifts:
        event_body = _make_event_body(shift)
        result = service.events().insert(
            calendarId="primary",
            body=event_body,
        ).execute()
        urls.append(result.get("htmlLink", ""))

    return urls


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_event_body(shift: dict) -> dict:
    """Build a Google Calendar API event dict from a single shift dict."""
    shift_date: date = shift["date"]
    start: time = shift["start"]
    end: time = shift["end"]
    title: str = shift.get("title", "Work Shift")

    dt_start = datetime.combine(shift_date, start)
    dt_end = datetime.combine(shift_date, end)

    # Handle overnight shifts (end before or equal to start)
    if dt_end <= dt_start:
        dt_end += timedelta(days=1)

    return {
        "summary": title,
        "start": {
            "dateTime": dt_start.isoformat(),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": dt_end.isoformat(),
            "timeZone": TIMEZONE,
        },
        "colorId": COLOR_ID,
    }
