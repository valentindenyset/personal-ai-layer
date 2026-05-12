"""Full re-ingestion from all enabled sources."""
from __future__ import annotations

import logging

import yaml

from config.settings import settings
from ingestion.pipeline import IngestionPipeline
from ingestion.sources.calendar import GoogleCalendarSource
from ingestion.sources.mail import GmailSource
from ingestion.sources.health import AppleHealthSource
from ingestion.sources.contacts import ContactsSource
from ingestion.sources.photos import PhotosMetadataSource
from ingestion.sources.gdpr_exports.whatsapp import WhatsAppExportSource
from ingestion.sources.gdpr_exports.instagram import InstagramExportSource
from ingestion.sources.macos.imessage import IMessageSource
from ingestion.sources.macos.notes import NotesSource
from stores.graph_store import GraphStore
from stores.vector_store import VectorStore

logger = logging.getLogger(__name__)


def run_full_sync():
    logger.info("starting FULL sync — this may take a while …")

    with open("config/sources.yaml") as f:
        cfg = yaml.safe_load(f)["sources"]

    vs = VectorStore()
    gs = GraphStore()
    pipeline = IngestionPipeline(vs, gs)
    all_docs = []

    def maybe(source_key: str, source_cls, *args, fetch_kwargs=None, **kwargs):
        if cfg.get(source_key, {}).get("enabled"):
            try:
                src = source_cls(*args, **kwargs)
                docs = src.fetch(**(fetch_kwargs or {}))
                all_docs.extend(docs)
                logger.info("%s: +%d docs", source_key, len(docs))
            except Exception as e:
                logger.error("%s failed: %s", source_key, e)

    maybe("google_calendar", GoogleCalendarSource,
          settings.google_client_id, settings.google_client_secret, settings.google_token_path,
          fetch_kwargs={"lookback_days": cfg.get("google_calendar", {}).get("lookback_days", 365)})

    maybe("google_mail", GmailSource,
          settings.google_client_id, settings.google_client_secret, settings.google_token_path,
          fetch_kwargs={
              "max_emails": cfg.get("google_mail", {}).get("max_emails", 5000),
              "labels": cfg.get("google_mail", {}).get("labels"),
          })

    maybe("apple_health", AppleHealthSource,
          cfg.get("apple_health", {}).get("export_path", "data/apple_health_export/export.xml"))

    maybe("macos_imessage", IMessageSource,
          cfg.get("macos_imessage", {}).get("db_path"),
          fetch_kwargs={"lookback_days": cfg.get("macos_imessage", {}).get("lookback_days", 730)})

    maybe("macos_notes", NotesSource,
          cfg.get("macos_notes", {}).get("export_dir", "data/notes_export"))

    maybe("gdpr_whatsapp", WhatsAppExportSource,
          cfg.get("gdpr_whatsapp", {}).get("export_dir", "data/gdpr_exports/whatsapp"))

    maybe("gdpr_instagram", InstagramExportSource,
          cfg.get("gdpr_instagram", {}).get("export_dir", "data/gdpr_exports/instagram"))

    stats = pipeline.run(all_docs)
    logger.info("full sync done: %s", stats)
    return stats
