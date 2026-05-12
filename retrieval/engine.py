"""Hybrid retrieval: vector similarity + graph traversal → fusion + reranking."""
from __future__ import annotations

from dataclasses import dataclass

from ingestion.embedder import get_embedder
from ingestion.entity_extractor import get_extractor
from stores.vector_store import VectorStore
from stores.graph_store import GraphStore
from .fusion import reciprocal_rank_fusion
from .reranker import Reranker


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str
    metadata: dict


class HybridRetrievalEngine:
    def __init__(self, vector_store: VectorStore, graph_store: GraphStore):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = get_embedder()
        self.extractor = get_extractor()
        self.reranker = Reranker()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        # 1. Vector search
        query_vec = self.embedder.embed(query)
        vector_results = self.vector_store.search(query_vec, top_k=top_k * 2, filters=filters)

        # 2. Graph expansion — find docs that mention query entities
        entities = self.extractor.extract(query)
        entity_names = [e["name"] for e in entities]
        graph_doc_ids: set[str] = set()
        for name in entity_names:
            graph_doc_ids.update(self.graph_store.get_entity_documents(name))

        # Fetch graph-expanded results from vector store
        graph_results: list[dict] = []
        for doc_id in list(graph_doc_ids)[:top_k]:
            results = self.vector_store.search(
                query_vec,
                top_k=3,
                filters={"doc_id": doc_id},
            )
            graph_results.extend(results)

        # 3. Fusion
        fused = reciprocal_rank_fusion(vector_results, graph_results)

        # 4. Rerank
        reranked = self.reranker.rerank(query, fused, top_k=top_k)

        return [
            RetrievedChunk(
                text=r["text"],
                score=r["score"],
                source=r.get("source", ""),
                metadata={k: v for k, v in r.items() if k not in {"text", "score", "source"}},
            )
            for r in reranked
        ]
