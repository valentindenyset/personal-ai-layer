"""CLI to ingest one-shot GDPR export archives."""
import logging
from pathlib import Path

import typer

from ingestion.pipeline import IngestionPipeline
from ingestion.sources.gdpr_exports.whatsapp import WhatsAppExportSource
from ingestion.sources.gdpr_exports.instagram import InstagramExportSource
from stores.graph_store import GraphStore
from stores.vector_store import VectorStore

app = typer.Typer()
logging.basicConfig(level=logging.INFO)


@app.command()
def whatsapp(export_dir: Path = typer.Argument(..., help="Path to unzipped WhatsApp export")):
    """Ingest a WhatsApp GDPR export."""
    vs, gs = VectorStore(), GraphStore()
    pipeline = IngestionPipeline(vs, gs)
    docs = WhatsAppExportSource(export_dir).fetch()
    stats = pipeline.run(docs)
    typer.echo(f"Done: {stats}")


@app.command()
def instagram(export_dir: Path = typer.Argument(..., help="Path to unzipped Instagram export")):
    """Ingest an Instagram GDPR export."""
    vs, gs = VectorStore(), GraphStore()
    pipeline = IngestionPipeline(vs, gs)
    docs = InstagramExportSource(export_dir).fetch()
    stats = pipeline.run(docs)
    typer.echo(f"Done: {stats}")


if __name__ == "__main__":
    app()
