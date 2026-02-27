"""
Gmail API client — handles OAuth2 authentication and email fetching.

Setup:
  1. Create a project at https://console.cloud.google.com/
  2. Enable the Gmail API
  3. Create OAuth2 credentials (Desktop App) and download as credentials.json
"""

import base64
import os
from email import message_from_bytes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# Edit this query to match your shift email's subject line
DEFAULT_SEARCH_QUERY = "subject:New shifts assigned at House Made Hospitality"


def get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found. "
                    "Download it from Google Cloud Console (OAuth2 Desktop App credentials) "
                    "and place it in the project root."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def search_emails(service, query: str = DEFAULT_SEARCH_QUERY, max_results: int = 5) -> list[dict]:
    """Search Gmail and return a list of message summaries."""
    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    if not messages:
        return []

    summaries = []
    for msg in messages:
        meta = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in meta["payload"]["headers"]}
        summaries.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
        })

    return summaries


def fetch_email_body(service, message_id: str) -> str:
    """Fetch and return the plain-text body of an email by ID."""
    msg = service.users().messages().get(
        userId="me",
        id=message_id,
        format="raw"
    ).execute()

    raw = base64.urlsafe_b64decode(msg["raw"].encode("utf-8"))
    email_msg = message_from_bytes(raw)

    return _extract_plain_text(email_msg)


def _extract_plain_text(msg) -> str:
    """Extract readable text from an email, preferring text/plain over text/html."""
    plain = None
    html = None

    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/plain" and plain is None:
            charset = part.get_content_charset() or "utf-8"
            plain = part.get_payload(decode=True).decode(charset, errors="replace")
        elif ct == "text/html" and html is None:
            charset = part.get_content_charset() or "utf-8"
            html = part.get_payload(decode=True).decode(charset, errors="replace")

    if plain:
        return plain
    if html:
        return _html_to_text(html)
    return ""


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text by stripping tags and mapping block elements to newlines."""
    from html.parser import HTMLParser

    class _Extractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)

        def handle_starttag(self, tag, attrs):
            if tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4"):
                self.parts.append("\n")

        def handle_endtag(self, tag):
            if tag in ("p", "div", "tr", "li", "h1", "h2", "h3", "h4"):
                self.parts.append("\n")

    extractor = _Extractor()
    extractor.feed(html)
    return "".join(extractor.parts)
