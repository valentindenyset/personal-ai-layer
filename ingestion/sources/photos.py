"""Photos source — ingests EXIF metadata only (no image content)."""
from __future__ import annotations

import logging
from pathlib import Path

from ingestion.pipeline import Document
from ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)


class PhotosMetadataSource:
    """
    Point to a folder exported from Photos.app (File > Export > Export Unmodified Originals).
    Only EXIF metadata is indexed — no pixel data.
    """

    def __init__(self, photos_dir: Path):
        self.photos_dir = Path(photos_dir).expanduser()
        self._extensions = {".jpg", ".jpeg", ".heic", ".png"}

    def fetch(self) -> list[Document]:
        if not self.photos_dir.exists():
            logger.warning("photos dir not found at %s — skipping", self.photos_dir)
            return []

        import exifread
        docs: list[Document] = []

        for path in self.photos_dir.rglob("*"):
            if path.suffix.lower() not in self._extensions:
                continue
            try:
                with path.open("rb") as f:
                    tags = exifread.process_file(f, details=False)
                doc = self._to_document(path, tags)
                if doc:
                    docs.append(doc)
            except Exception as exc:
                logger.debug("could not read EXIF from %s: %s", path, exc)

        logger.info("photos: indexed %d photos", len(docs))
        return docs

    def _to_document(self, path: Path, tags: dict) -> Document | None:
        date = str(tags.get("EXIF DateTimeOriginal", "")).strip()
        gps_lat = str(tags.get("GPS GPSLatitude", "")).strip()
        gps_lon = str(tags.get("GPS GPSLongitude", "")).strip()
        make = str(tags.get("Image Make", "")).strip()
        model = str(tags.get("Image Model", "")).strip()
        parts = [f"Photo: {path.name}", f"Date: {date}"]
        if gps_lat:
            parts.append(f"Location: {gps_lat}, {gps_lon}")
        if make:
            parts.append(f"Camera: {make} {model}")
        return Document(
            source="photos",
            doc_id=Deduplicator.stable_id("photos", path.name),
            content="\n".join(parts),
            metadata={"filename": path.name, "date": date},
        )
