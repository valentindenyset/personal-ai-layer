"""Google Calendar source — fetches events via the Google Calendar API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class GoogleCalendarSource:
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self, client_id: str, client_secret: str, token_path: Path):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = token_path

    def _build_service(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {"installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }},
                    self.SCOPES,
                )
                creds = flow.run_local_server(port=0)
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    def fetch(self, lookback_days: int = 365) -> list[Document]:
        service = self._build_service()
        since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
        docs: list[Document] = []

        calendars = service.calendarList().list().execute().get("items", [])
        for cal in calendars:
            cal_id = cal["id"]
            page_token = None
            while True:
                resp = service.events().list(
                    calendarId=cal_id,
                    timeMin=since,
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token,
                    maxResults=250,
                ).execute()
                for event in resp.get("items", []):
                    doc = self._to_document(event, cal["summary"])
                    if doc:
                        docs.append(doc)
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

        logger.info("google_calendar: fetched %d events", len(docs))
        return docs

    def _to_document(self, event: dict, calendar_name: str) -> Document | None:
        summary = event.get("summary", "")
        description = event.get("description", "")
        attendees = ", ".join(a.get("email", "") for a in event.get("attendees", []))
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date", "")
        content = f"[Calendar: {calendar_name}] {summary}\nDate: {start}\nAttendees: {attendees}\n{description}".strip()
        if not content:
            return None
        return Document(
            source="google_calendar",
            doc_id=Deduplicator.stable_id("google_calendar", event["id"]),
            content=content,
            metadata={"calendar": calendar_name, "event_id": event["id"], "start": start},
        )
