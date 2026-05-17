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
    # Will implement in next task
    pass
