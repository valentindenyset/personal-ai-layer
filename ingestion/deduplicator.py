"""Prevents re-ingesting documents already in the store."""
from __future__ import annotations

import hashlib


class Deduplicator:
    def __init__(self, vector_store):
        self._store = vector_store

    def is_duplicate(self, doc) -> bool:
        return self._store.doc_exists(doc.doc_id)

    @staticmethod
    def stable_id(source: str, raw_id: str) -> str:
        return hashlib.sha256(f"{source}:{raw_id}".encode()).hexdigest()[:16]
