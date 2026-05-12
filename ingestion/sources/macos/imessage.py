"""
iMessage source — reads directly from macOS Messages SQLite database.

Requirements:
  - macOS only
  - Grant "Full Disk Access" to Terminal (or your Python runtime) in:
    System Settings > Privacy & Security > Full Disk Access
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

# Apple timestamps are seconds since 2001-01-01 (Cocoa epoch)
COCOA_EPOCH = datetime(2001, 1, 1)
CHUNK_MESSAGES = 50


class IMessageSource:
    DEFAULT_DB = Path("~/Library/Messages/chat.db")

    def __init__(self, db_path: Path | None = None, lookback_days: int = 730):
        self.db_path = Path(db_path or self.DEFAULT_DB).expanduser()
        self.lookback_days = lookback_days

    def fetch(self) -> list[Document]:
        if not self.db_path.exists():
            logger.warning("iMessage DB not found at %s — grant Full Disk Access to Terminal", self.db_path)
            return []

        cutoff_ts = (datetime.now() - timedelta(days=self.lookback_days) - COCOA_EPOCH).total_seconds() * 1e9

        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        except sqlite3.OperationalError as e:
            logger.error("cannot open iMessage DB: %s", e)
            return []

        sql = """
            SELECT
                h.id          AS contact,
                m.date        AS ts,
                m.is_from_me  AS from_me,
                m.text        AS body
            FROM message m
            JOIN handle h ON h.ROWID = m.handle_id
            WHERE m.text IS NOT NULL
              AND m.date > ?
            ORDER BY h.id, m.date
        """
        rows = conn.execute(sql, (cutoff_ts,)).fetchall()
        conn.close()

        conversations: dict[str, list[str]] = {}
        for contact, ts, from_me, body in rows:
            dt = COCOA_EPOCH + timedelta(seconds=ts / 1e9)
            label = "Me" if from_me else contact
            conversations.setdefault(contact, []).append(f"[{dt:%Y-%m-%d %H:%M}] {label}: {body}")

        docs: list[Document] = []
        for contact, lines in conversations.items():
            for i in range(0, len(lines), CHUNK_MESSAGES):
                chunk_lines = lines[i:i + CHUNK_MESSAGES]
                docs.append(Document(
                    source="imessage",
                    doc_id=Deduplicator.stable_id("imessage", f"{contact}:{i}"),
                    content=f"[iMessage: {contact}]\n" + "\n".join(chunk_lines),
                    metadata={"contact": contact, "chunk_index": i // CHUNK_MESSAGES},
                ))

        logger.info("imessage: produced %d documents from %d conversations", len(docs), len(conversations))
        return docs
