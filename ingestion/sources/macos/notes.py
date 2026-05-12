"""
Apple Notes source.

Approach A (recommended): Export via the provided AppleScript.
  Run: osascript scripts/export_notes.applescript
  Output lands in data/notes_export/*.txt

Approach B: Shortcuts app on iPhone/Mac
  Create a shortcut: Get All Notes → Repeat → Get Text from Note → Save to Files
"""
from __future__ import annotations

import logging
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class NotesSource:
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir).expanduser()

    def fetch(self) -> list[Document]:
        if not self.export_dir.exists():
            logger.warning(
                "notes export dir not found at %s — run: osascript scripts/export_notes.applescript",
                self.export_dir,
            )
            return []

        docs: list[Document] = []
        for note_file in self.export_dir.glob("*.txt"):
            text = note_file.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                continue
            docs.append(Document(
                source="notes",
                doc_id=Deduplicator.stable_id("notes", note_file.stem),
                content=f"[Note: {note_file.stem}]\n{text}",
                metadata={"title": note_file.stem, "filename": note_file.name},
            ))

        logger.info("notes: loaded %d notes", len(docs))
        return docs
