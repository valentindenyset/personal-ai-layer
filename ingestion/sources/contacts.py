"""Contacts source — reads vCard files exported from Contacts.app."""
from __future__ import annotations

import logging
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class ContactsSource:
    """
    Export contacts from Contacts.app:
      File > Export > Export vCard…  → save to data/contacts/contacts.vcf
    """

    def __init__(self, vcf_path: Path):
        self.vcf_path = Path(vcf_path).expanduser()

    def fetch(self) -> list[Document]:
        if not self.vcf_path.exists():
            logger.warning("contacts vCard not found at %s — skipping", self.vcf_path)
            return []

        import vobject
        docs: list[Document] = []
        raw = self.vcf_path.read_text(encoding="utf-8", errors="replace")

        for vcard in vobject.readComponents(raw):
            doc = self._to_document(vcard)
            if doc:
                docs.append(doc)

        logger.info("contacts: loaded %d contacts", len(docs))
        return docs

    def _to_document(self, vcard) -> Document | None:
        name = str(getattr(vcard, "fn", "")).strip()
        if not name:
            return None
        parts = [f"Contact: {name}"]
        if hasattr(vcard, "email"):
            parts.append(f"Email: {vcard.email.value}")
        if hasattr(vcard, "tel"):
            parts.append(f"Phone: {vcard.tel.value}")
        if hasattr(vcard, "org"):
            parts.append(f"Org: {vcard.org.value}")
        return Document(
            source="contacts",
            doc_id=Deduplicator.stable_id("contacts", name),
            content="\n".join(parts),
            metadata={"name": name},
        )
