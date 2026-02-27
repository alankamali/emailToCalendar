"""
emailToCalendar — main entry point.

Usage:
  python main.py                          # Fetch from Gmail and pick an email
  python main.py --file sample_email.txt  # Parse a local text file instead
  python main.py --query "subject:rota"   # Override the Gmail search query
  python main.py --week 2025-03-03        # Specify the week's Monday date (YYYY-MM-DD)
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from shift_parser import parse_shifts
from calendar_generator import generate_ics


def main():
    args = _parse_args()

    # Resolve the reference Monday for the shift week
    week_monday = None
    if args.week:
        try:
            week_monday = date.fromisoformat(args.week)
            if week_monday.weekday() != 0:
                print(f"Warning: {args.week} is not a Monday. Shifts will still be parsed using day names.")
        except ValueError:
            print(f"Error: --week must be in YYYY-MM-DD format (e.g. --week 2025-03-03)")
            sys.exit(1)

    # Get the email body
    if args.file:
        body = _read_file(args.file)
    else:
        body = _fetch_from_gmail(args.query)

    if not body:
        print("Error: No email body found.")
        sys.exit(1)

    # Parse and generate
    print("\nParsing shifts...")
    shifts = parse_shifts(body, _reference_date=week_monday)

    if not shifts:
        print("\nNo shifts were found. Check that your email format matches the parser.")
        print("Tip: Share a sample email and update shift_parser.py to match the format.")
        sys.exit(1)

    print(f"\nFound {len(shifts)} shift(s):")
    for s in shifts:
        print(f"  {s['date'].strftime('%A, %d %b %Y')}  {s['start'].strftime('%H:%M')} – {s['end'].strftime('%H:%M')}")

    output_path = generate_ics(shifts)
    print(f"\nCalendar file written: {output_path.resolve()}")
    print("Import it into Google Calendar: Settings → Import & Export → Import")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Parse a shift schedule email and generate a .ics calendar file."
    )
    parser.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to a plain-text file containing the email body (skips Gmail).",
    )
    parser.add_argument(
        "--query", "-q",
        metavar="QUERY",
        help="Gmail search query to find shift emails (overrides default).",
    )
    parser.add_argument(
        "--week", "-w",
        metavar="YYYY-MM-DD",
        help="The Monday of the shift week (helps resolve day names to dates).",
    )
    return parser.parse_args()


def _read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def _fetch_from_gmail(query: str | None) -> str:
    try:
        from gmail_client import get_gmail_service, search_emails, fetch_email_body, DEFAULT_SEARCH_QUERY
    except ImportError as e:
        print(f"Error importing Gmail client: {e}")
        sys.exit(1)

    search_query = query or DEFAULT_SEARCH_QUERY

    print("Connecting to Gmail...")
    service = get_gmail_service()

    print(f"Searching for emails matching: {search_query!r}")
    emails = search_emails(service, query=search_query)

    if not emails:
        print(f"No emails found matching the query: {search_query!r}")
        print("Try adjusting the query with --query, e.g.: --query 'subject:your shift'")
        sys.exit(1)

    # Let the user pick an email
    print(f"\nFound {len(emails)} email(s):\n")
    for i, email in enumerate(emails, start=1):
        print(f"  [{i}] {email['date']}")
        print(f"      From: {email['from']}")
        print(f"      Subject: {email['subject']}\n")

    if len(emails) == 1:
        choice = 1
        print(f"Using the only result: [{choice}]")
    else:
        while True:
            raw = input(f"Select an email [1-{len(emails)}] (default: 1): ").strip()
            if raw == "":
                choice = 1
                break
            if raw.isdigit() and 1 <= int(raw) <= len(emails):
                choice = int(raw)
                break
            print(f"Please enter a number between 1 and {len(emails)}.")

    selected = emails[choice - 1]
    print(f"\nFetching email: {selected['subject']!r}")
    return fetch_email_body(service, selected["id"])


if __name__ == "__main__":
    main()
