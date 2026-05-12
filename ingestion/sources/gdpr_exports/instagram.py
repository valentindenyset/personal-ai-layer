"""
Instagram GDPR export parser.

How to export:
  Settings > Account Center > Your information and permissions >
  Download your information > Select: Messages, Comments, Posts → JSON format

Place the unzipped folder at data/gdpr_exports/instagram/.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class InstagramExportSource:
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir).expanduser()

    def fetch(self) -> list[Document]:
        if not self.export_dir.exists():
            logger.warning("instagram export not found at %s — skipping", self.export_dir)
            return []

        docs: list[Document] = []
        docs.extend(self._parse_messages())
        docs.extend(self._parse_comments())
        logger.info("instagram: produced %d documents", len(docs))
        return docs

    def _parse_messages(self) -> list[Document]:
        inbox = self.export_dir / "messages" / "inbox"
        if not inbox.exists():
            return []
        docs: list[Document] = []
        for thread_dir in inbox.iterdir():
            for json_file in thread_dir.glob("message_*.json"):
                try:
                    data = json.loads(json_file.read_bytes())
                    doc = self._thread_to_doc(data, thread_dir.name)
                    if doc:
                        docs.append(doc)
                except Exception as exc:
                    logger.debug("could not parse %s: %s", json_file, exc)
        return docs

    def _thread_to_doc(self, data: dict, thread_name: str) -> Document | None:
        participants = ", ".join(p.get("name", "") for p in data.get("participants", []))
        messages = data.get("messages", [])
        lines = []
        for msg in messages[-100:]:  # last 100 messages per file
            sender = msg.get("sender_name", "")
            content = msg.get("content", "")
            ts = msg.get("timestamp_ms", 0) // 1000
            if content:
                lines.append(f"[{ts}] {sender}: {content}")
        if not lines:
            return None
        text = f"[Instagram DM: {participants}]\n" + "\n".join(lines)
        return Document(
            source="instagram",
            doc_id=Deduplicator.stable_id("instagram", thread_name),
            content=text,
            metadata={"thread": thread_name, "participants": participants},
        )

    def _parse_comments(self) -> list[Document]:
        comments_file = self.export_dir / "comments" / "post_comments_1.json"
        if not comments_file.exists():
            return []
        data = json.loads(comments_file.read_bytes())
        lines = []
        for entry in data:
            for item in entry.get("string_list_data", []):
                value = item.get("value", "").strip()
                ts = item.get("timestamp", 0)
                if value:
                    lines.append(f"[{ts}] Comment: {value}")
        if not lines:
            return []
        return [Document(
            source="instagram",
            doc_id=Deduplicator.stable_id("instagram", "comments"),
            content="[Instagram comments]\n" + "\n".join(lines),
            metadata={"type": "comments"},
        )]
