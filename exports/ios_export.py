"""Export Qdrant vectors + Neo4j graph to SQLite for iOS."""
from __future__ import annotations
import sqlite3
import struct
from pathlib import Path
from typing import Any

from stores.vector_store import VectorStore
from stores.graph_store import GraphStore
from .graph_serializer import export_graph_json


def export_for_ios(
    vector_store: VectorStore,
    graph_store: GraphStore,
    output_path: str,
) -> dict[str, Any]:
    """
    Export vector store and graph to iOS-compatible format.

    Args:
        vector_store: Qdrant vector store instance
        graph_store: Neo4j graph store instance
        output_path: Path for output .db file (without extension)

    Returns:
        Dict with paths to exported files
    """
    db_path = f"{output_path}.db"
    output_dir = str(Path(output_path).parent)

    # Export vectors to SQLite
    _export_vectors_to_sqlite(vector_store, db_path)

    # Export graph to JSON
    entities_path, relations_path = export_graph_json(graph_store, output_dir)

    return {
        "database": db_path,
        "entities": entities_path,
        "relations": relations_path,
    }


def export_delta(
    vector_store: VectorStore,
    graph_store: GraphStore,
    output_path: str,
    since_ts: float,
) -> dict[str, Any]:
    """Export only changes since timestamp (for incremental updates)."""
    # For MVP, not implemented - just call full export
    return export_for_ios(vector_store, graph_store, output_path)


def _export_vectors_to_sqlite(vector_store: VectorStore, db_path: str) -> None:
    """Export chunks with embeddings to SQLite."""
    import json

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            embedding BLOB,
            source TEXT NOT NULL,
            date_ts REAL DEFAULT 0,
            metadata_json TEXT,
            origin TEXT DEFAULT 'bulk_import',
            created_at INTEGER DEFAULT (unixepoch())
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_date ON chunks(date_ts DESC)")

    # Create contacts table for phone resolution
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            phone_suffix TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            full_phone TEXT,
            email TEXT,
            last_updated_ts REAL DEFAULT (unixepoch())
        )
    """)

    # Fetch all chunks from Qdrant
    chunks = _fetch_all_chunks(vector_store)

    # Insert chunks
    for chunk in chunks:
        # Pack embedding as binary blob (384 floats = 1536 bytes)
        embedding_blob = None
        if chunk.get("embedding"):
            embedding_blob = struct.pack(f"{len(chunk['embedding'])}f", *chunk["embedding"])

        # Convert metadata to JSON
        metadata_json = json.dumps(chunk.get("metadata", {}))

        cursor.execute(
            """INSERT INTO chunks (text, embedding, source, date_ts, metadata_json, origin)
               VALUES (?, ?, ?, ?, ?, 'bulk_import')""",
            (
                chunk["text"],
                embedding_blob,
                chunk.get("source", ""),
                chunk.get("date_ts", 0.0),
                metadata_json,
            )
        )

    conn.commit()

    # Vacuum to compress
    cursor.execute("VACUUM")

    conn.close()


def _fetch_all_chunks(vector_store: VectorStore) -> list[dict]:
    """Fetch all chunks from Qdrant vector store."""
    chunks = []

    # Handle mock for tests
    if hasattr(vector_store, 'chunks'):
        return vector_store.chunks

    offset = None
    batch_size = 1000

    while True:
        # Scroll through Qdrant
        result = vector_store._client.scroll(
            collection_name=vector_store._collection,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        points, next_offset = result

        if not points:
            break

        for point in points:
            chunks.append({
                "text": point.payload.get("text", ""),
                "embedding": point.vector,
                "source": point.payload.get("source", ""),
                "date_ts": point.payload.get("date_ts", 0.0),
                "metadata": {k: v for k, v in point.payload.items()
                           if k not in ["text", "source", "date_ts"]},
            })

        if next_offset is None:
            break
        offset = next_offset

    return chunks
