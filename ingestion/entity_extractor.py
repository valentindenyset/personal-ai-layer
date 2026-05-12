"""Named-entity recognition: Person, Place, Event, Concept."""
from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# spaCy label → graph node type mapping
LABEL_MAP = {
    "PER": "Person",
    "PERSON": "Person",
    "ORG": "Organization",
    "GPE": "Place",
    "LOC": "Place",
    "EVENT": "Event",
    "DATE": "Date",
    "TIME": "Time",
    "MISC": "Concept",
    "PRODUCT": "Concept",
}


class EntityExtractor:
    def __init__(self, model: str = "fr_core_news_lg"):
        self._model_name = model
        self._nlp = None  # lazy-load

    def _load(self):
        if self._nlp is None:
            import spacy
            try:
                self._nlp = spacy.load(self._model_name)
            except OSError:
                logger.warning("spaCy model %s not found — run: python -m spacy download %s",
                               self._model_name, self._model_name)
                self._nlp = None

    def extract(self, text: str) -> list[dict]:
        self._load()
        if self._nlp is None:
            return []
        doc = self._nlp(text[:10_000])  # spaCy has a practical limit
        entities = []
        seen: set[str] = set()
        for ent in doc.ents:
            node_type = LABEL_MAP.get(ent.label_, "Concept")
            key = f"{node_type}:{ent.text.strip().lower()}"
            if key not in seen:
                seen.add(key)
                entities.append({"type": node_type, "name": ent.text.strip(), "label": ent.label_})
        return entities


@lru_cache(maxsize=1)
def get_extractor() -> EntityExtractor:
    return EntityExtractor()
