"""
Shift parser — converts raw Employment Hero email body into structured shift data.

Expected email format (from no-reply@employmenthero.com):

  1. Work Site: (CAR) Carrington FOH
  Position: Bartender
  Date: 02/03/2026
  Time: 03:00 PM - 11:00 PM
  Click here to view your shift.

Returns a list of dicts:
  {"date": datetime.date, "start": datetime.time, "end": datetime.time, "title": str}
"""

import re
from datetime import date, time, datetime

# ---------------------------------------------------------------------------
# Patterns tuned to the Employment Hero email format
# ---------------------------------------------------------------------------

# Marks the start of a new shift block: "1. Work Site: ..."
SHIFT_BLOCK_RE = re.compile(r"^\d+\.\s+Work Site:", re.IGNORECASE | re.MULTILINE)

# "Date: DD/MM/YYYY"
DATE_LINE_RE = re.compile(r"^Date:\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE)

# "Time: 03:00 PM - 11:00 PM"
TIME_LINE_RE = re.compile(
    r"^Time:\s*(\d{1,2}:\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}:\d{2})\s*(AM|PM)",
    re.IGNORECASE,
)

# "Position: Bartender"
POSITION_RE = re.compile(r"^Position:\s*(.+)", re.IGNORECASE)

# "Work Site: (CAR) Carrington FOH"
WORK_SITE_RE = re.compile(r"^Work Site:\s*(.+)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_shifts(body: str, _reference_date: date | None = None) -> list[dict]:
    """
    Parse shift blocks from an Employment Hero email body.

    Args:
        body: Raw email text.
        _reference_date: Unused — dates are explicit in this format. Kept for
                         API compatibility with main.py.

    Returns:
        List of shift dicts with keys: date, start, end, title.
    """
    shifts = []

    # Split body on each numbered shift header ("1. Work Site:", "2. Work Site:", ...)
    # The split consumes the delimiter, so re-attach "Work Site:" to each block.
    blocks = SHIFT_BLOCK_RE.split(body)
    shift_blocks = blocks[1:]  # blocks[0] is the preamble — discard it

    for block in shift_blocks:
        shift = _parse_block("Work Site:" + block)
        if shift:
            shifts.append(shift)

    if not shifts:
        print("[parser] No shifts found. Check that the email body matches the Employment Hero format.")

    return shifts


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_block(block: str) -> dict | None:
    """Parse a single shift block into a shift dict, or None on failure."""
    shift_date = None
    start_time = None
    end_time = None
    position = None
    work_site = None

    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue

        if m := WORK_SITE_RE.match(line):
            work_site = m.group(1).strip()
        elif m := POSITION_RE.match(line):
            position = m.group(1).strip()
        elif m := DATE_LINE_RE.match(line):
            shift_date = _parse_date(m.group(1))
        elif m := TIME_LINE_RE.match(line):
            start_time = _parse_time(m.group(1), m.group(2))
            end_time = _parse_time(m.group(3), m.group(4))

    if shift_date is None or start_time is None or end_time is None:
        return None

    # Build a descriptive title from Position and Work Site
    parts = [p for p in [position, work_site] if p]
    title = " @ ".join(parts) if parts else "Work Shift"

    return {"date": shift_date, "start": start_time, "end": end_time, "title": title}


def _parse_date(date_str: str) -> date | None:
    """Parse DD/MM/YYYY into a date object."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None


def _parse_time(time_str: str, ampm: str) -> time | None:
    """Parse 'HH:MM' + 'AM'/'PM' into a time object."""
    try:
        return datetime.strptime(f"{time_str} {ampm.upper()}", "%I:%M %p").time()
    except ValueError:
        return None
