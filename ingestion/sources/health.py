"""Apple Health source — parses the XML export from the Health app."""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

# Metrics we care about for the agent's context
TRACKED_TYPES = {
    "HKQuantityTypeIdentifierStepCount": "Steps",
    "HKQuantityTypeIdentifierHeartRate": "Heart rate",
    "HKQuantityTypeIdentifierBodyMass": "Weight",
    "HKQuantityTypeIdentifierSleepAnalysis": "Sleep",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "Active calories",
    "HKCategoryTypeIdentifierMindfulSession": "Mindfulness",
}


class AppleHealthSource:
    def __init__(self, export_path: Path):
        self.export_path = Path(export_path).expanduser()

    def fetch(self) -> list[Document]:
        if not self.export_path.exists():
            logger.warning("Apple Health export not found at %s — skipping", self.export_path)
            return []

        logger.info("parsing Apple Health export …")
        tree = ET.parse(self.export_path)
        root = tree.getroot()

        daily: dict[str, dict[str, list[str]]] = {}  # date → type → values

        for record in root.iter("Record"):
            rtype = record.get("type", "")
            label = TRACKED_TYPES.get(rtype)
            if not label:
                continue
            date = (record.get("startDate") or record.get("creationDate") or "")[:10]
            value = record.get("value", "")
            unit = record.get("unit", "")
            if date:
                daily.setdefault(date, {}).setdefault(label, []).append(f"{value} {unit}".strip())

        docs: list[Document] = []
        for date, metrics in sorted(daily.items()):
            lines = [f"- {k}: {', '.join(v[:5])}" for k, v in metrics.items()]
            content = f"[Health] {date}\n" + "\n".join(lines)
            docs.append(Document(
                source="apple_health",
                doc_id=Deduplicator.stable_id("apple_health", date),
                content=content,
                metadata={"date": date},
            ))

        logger.info("apple_health: produced %d daily summaries", len(docs))
        return docs
