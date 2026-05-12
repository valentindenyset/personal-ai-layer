"""Orchestrates the full ingestion flow: source → chunk → embed → extract → store."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from .chunker import Chunker
from .deduplicator import Deduplicator
from .embedder import Embedder
from .entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Raw document produced by any source."""
    source: str                         # e.g. "google_calendar", "whatsapp"
    doc_id: str                         # stable unique id for dedup
    content: str
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Chunk:
    doc_id: str
    chunk_index: int
    text: str
    embedding: list[float] = field(default_factory=list)
    entities: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class IngestionPipeline:
    def __init__(self, vector_store, graph_store):
        self.chunker = Chunker()
        self.embedder = Embedder()
        self.extractor = EntityExtractor()
        self.deduplicator = Deduplicator(vector_store)
        self.vector_store = vector_store
        self.graph_store = graph_store

    def run(self, documents: list[Document]) -> dict:
        stats = {"ingested": 0, "skipped_duplicates": 0, "chunks": 0}

        for doc in documents:
            if self.deduplicator.is_duplicate(doc):
                stats["skipped_duplicates"] += 1
                continue

            raw_chunks = self.chunker.chunk(doc)
            texts = [c.text for c in raw_chunks]
            embeddings = self.embedder.embed_batch(texts)

            for chunk, embedding in zip(raw_chunks, embeddings):
                chunk.embedding = embedding
                chunk.entities = self.extractor.extract(chunk.text)

            self.vector_store.upsert_chunks(raw_chunks)
            self.graph_store.upsert_entities_from_chunks(raw_chunks, doc)

            stats["ingested"] += 1
            stats["chunks"] += len(raw_chunks)
            logger.info("ingested %s (%d chunks)", doc.doc_id, len(raw_chunks))

        return stats
