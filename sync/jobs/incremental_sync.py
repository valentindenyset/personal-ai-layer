"""Incremental sync — only fetches data newer than the last run."""
from __future__ import annotations

import logging

import yaml

from config.settings import settings
from ingestion.pipeline import IngestionPipeline
from ingestion.sources.calendar import GoogleCalendarSource
from ingestion.sources.mail import GmailSource
from ingestion.sources.health import AppleHealthSource
from stores.graph_store import GraphStore
from stores.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_incremental_sync():
    logger.info("starting incremental sync …")

    with open("config/sources.yaml") as f:
        cfg = yaml.safe_load(f)["sources"]

    vs = VectorStore()
    gs = GraphStore()
    pipeline = IngestionPipeline(vs, gs)

    all_docs = []

    if cfg.get("google_calendar", {}).get("enabled"):
        source = GoogleCalendarSource(
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_token_path,
        )
        all_docs.extend(source.fetch(lookback_days=cfg["google_calendar"].get("lookback_days", 365)))

    if cfg.get("google_mail", {}).get("enabled"):
        source = GmailSource(
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_token_path,
        )
        all_docs.extend(source.fetch(
            max_emails=cfg["google_mail"].get("max_emails", 1000),
            labels=cfg["google_mail"].get("labels"),
        ))

    if cfg.get("apple_health", {}).get("enabled"):
        source = AppleHealthSource(cfg["apple_health"]["export_path"])
        all_docs.extend(source.fetch())

    stats = pipeline.run(all_docs)
    logger.info("incremental sync done: %s", stats)
    return stats
