"""Stage 2 — action tool: create a Google Calendar event."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from config.settings import settings


class CalendarActionTool:
    def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        attendees: list[str] | None = None,
    ) -> dict:
        service = self._build_service()
        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Paris"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Paris"},
        }
        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]

        result = service.events().insert(calendarId="primary", body=event_body).execute()
        return {"event_id": result["id"], "link": result.get("htmlLink")}

    def _build_service(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        token_path = settings.google_token_path
        creds = Credentials.from_authorized_user_file(
            str(token_path),
            ["https://www.googleapis.com/auth/calendar"],
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("calendar", "v3", credentials=creds)
