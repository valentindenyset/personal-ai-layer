"""
WhatsApp GDPR export parser.

How to export:
  Settings > Account > Request account info  (full RGPD export, takes a few days)
  OR: open a chat > More > Export chat > Without media → _chat.txt

Place the unzipped folder at data/gdpr_exports/whatsapp/.
Each subfolder = one conversation (folder name = contact/group name).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

# e.g. "25/12/2023, 14:32 - Alice: Hello!"
MSG_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})(?::\d{2})?\s+-\s+([^:]+):\s+(.+)$"
)
CHUNK_MESSAGES = 50  # group N messages per document


class WhatsAppExportSource:
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir).expanduser()

    def fetch(self) -> list[Document]:
        if not self.export_dir.exists():
            logger.warning("whatsapp export not found at %s — skipping", self.export_dir)
            return []

        docs: list[Document] = []
        for chat_file in self.export_dir.rglob("_chat.txt"):
            conversation_name = chat_file.parent.name
            docs.extend(self._parse_chat(chat_file, conversation_name))

        # Also handle single-file exports
        for chat_file in self.export_dir.glob("*.txt"):
            conversation_name = chat_file.stem
            docs.extend(self._parse_chat(chat_file, conversation_name))

        logger.info("whatsapp: produced %d documents", len(docs))
        return docs

    def _parse_chat(self, path: Path, conversation: str) -> list[Document]:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        messages: list[str] = []
        docs: list[Document] = []

        for line in lines:
            m = MSG_PATTERN.match(line)
            if m:
                date, time, sender, text = m.groups()
                messages.append(f"[{date} {time}] {sender}: {text}")

            if len(messages) >= CHUNK_MESSAGES:
                docs.append(self._make_doc(conversation, messages, len(docs)))
                messages = []

        if messages:
            docs.append(self._make_doc(conversation, messages, len(docs)))

        return docs

    def _make_doc(self, conversation: str, messages: list[str], idx: int) -> Document:
        content = f"[WhatsApp: {conversation}]\n" + "\n".join(messages)
        return Document(
            source="whatsapp",
            doc_id=Deduplicator.stable_id("whatsapp", f"{conversation}:{idx}"),
            content=content,
            metadata={"conversation": conversation, "chunk_index": idx},
        )
