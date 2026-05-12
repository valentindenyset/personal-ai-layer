"""Local embeddings via sentence-transformers (multilingual, no API calls)."""
from __future__ import annotations

import logging
from functools import lru_cache

from config.settings import settings

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.embedding_model
        self._model = None  # lazy-load

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("loading embedding model %s", self._model_name)
            self._model = SentenceTransformer(self._model_name)

    def embed(self, text: str) -> list[float]:
        self._load()
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load()
        return self._model.encode(texts, normalize_embeddings=True, batch_size=64).tolist()


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder()
