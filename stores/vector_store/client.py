"""Qdrant vector store wrapper."""
from __future__ import annotations

import logging
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from config.settings import settings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self._client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._collection = settings.qdrant_collection
        self._dim = settings.embedding_dim

    def ensure_collection(self):
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )
            logger.info("created Qdrant collection '%s'", self._collection)

    def doc_exists(self, doc_id: str) -> bool:
        result = self._client.scroll(
            collection_name=self._collection,
            scroll_filter=Filter(must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]),
            limit=1,
        )
        return len(result[0]) > 0

    def upsert_chunks(self, chunks) -> None:
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=chunk.embedding,
                payload={
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    **chunk.metadata,
                },
            )
            for chunk in chunks
            if chunk.embedding
        ]
        if points:
            self._client.upsert(collection_name=self._collection, points=points)

    def search(self, query_vector: list[float], top_k: int = 10, filters: dict | None = None) -> list[dict]:
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [{"score": r.score, **r.payload} for r in results]
