"""Gmail source — fetches emails via the Gmail API."""
from __future__ import annotations

import base64
import logging
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class GmailSource:
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

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
        return build("gmail", "v1", credentials=creds)

    def fetch(self, max_emails: int = 5000, labels: list[str] | None = None) -> list[Document]:
        service = self._build_service()
        labels = labels or ["INBOX"]
        docs: list[Document] = []

        for label in labels:
            page_token = None
            fetched = 0
            while fetched < max_emails:
                resp = service.users().messages().list(
                    userId="me",
                    labelIds=[label],
                    maxResults=min(100, max_emails - fetched),
                    pageToken=page_token,
                ).execute()
                for msg_ref in resp.get("messages", []):
                    msg = service.users().messages().get(
                        userId="me", id=msg_ref["id"], format="full"
                    ).execute()
                    doc = self._to_document(msg, label)
                    if doc:
                        docs.append(doc)
                    fetched += 1
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

        logger.info("gmail: fetched %d emails", len(docs))
        return docs

    def _to_document(self, msg: dict, label: str) -> Document | None:
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        date = headers.get("Date", "")
        body = self._extract_body(msg.get("payload", {}))
        content = f"[Email] From: {sender}\nDate: {date}\nSubject: {subject}\n\n{body}".strip()
        if not content:
            return None
        return Document(
            source="gmail",
            doc_id=Deduplicator.stable_id("gmail", msg["id"]),
            content=content[:8000],  # cap at 8k chars
            metadata={"label": label, "message_id": msg["id"], "subject": subject, "from": sender},
        )

    def _extract_body(self, payload: dict) -> str:
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            # Recurse into multipart
            for part in payload["parts"]:
                result = self._extract_body(part)
                if result:
                    return result
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""
