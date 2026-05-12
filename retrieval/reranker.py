"""Cross-encoder reranker (falls back to score passthrough if model unavailable)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Reranker:
    MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.MODEL)
            except Exception as e:
                logger.warning("cross-encoder not available (%s) — using score passthrough", e)

    def rerank(self, query: str, results: list[dict], top_k: int = 10) -> list[dict]:
        self._load()
        if not results:
            return results

        if self._model is None:
            return results[:top_k]

        pairs = [(query, r.get("text", "")) for r in results]
        scores = self._model.predict(pairs)
        for result, score in zip(results, scores):
            result["score"] = float(score)

        return sorted(results, key=lambda r: r["score"], reverse=True)[:top_k]
