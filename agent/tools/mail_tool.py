"""Stage 2 — action tool: send an email via Gmail."""
from __future__ import annotations

import base64
from email.mime.text import MIMEText

from config.settings import settings


class MailActionTool:
    def send_email(self, to: str, subject: str, body: str) -> dict:
        service = self._build_service()
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return {"message_id": result["id"]}

    def _build_service(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            str(settings.google_token_path),
            ["https://www.googleapis.com/auth/gmail.send"],
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)
