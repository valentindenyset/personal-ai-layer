"""Tests for iOS export functionality."""
import pytest
import sqlite3
import struct
from exports.ios_export import _export_vectors_to_sqlite


def test_export_vectors_creates_sqlite_with_chunks(tmp_path, mock_vector_store):
    """Test that vector export creates SQLite with chunks table."""
    db_path = str(tmp_path / "test.db")

    # Mock vector store with test data
    mock_vector_store.chunks = [
        {
            "text": "Test message",
            "embedding": [0.1] * 384,
            "source": "messages/test/chunk_1",
            "date_ts": 1715875200.0,
            "metadata": {"sender": "Test"}
        }
    ]

    _export_vectors_to_sqlite(mock_vector_store, db_path)

    # Verify database structure
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
    assert cursor.fetchone() is not None

    # Check data
    cursor.execute("SELECT text, source, date_ts FROM chunks")
    row = cursor.fetchone()
    assert row[0] == "Test message"
    assert row[1] == "messages/test/chunk_1"
    assert row[2] == 1715875200.0

    conn.close()


def test_export_vectors_stores_embeddings_as_blob(tmp_path, mock_vector_store):
    """Test that embeddings are stored as BLOB of floats."""
    db_path = str(tmp_path / "test.db")

    embedding = [0.5, 0.3, 0.8] + [0.0] * 381
    mock_vector_store.chunks = [{
        "text": "Test",
        "embedding": embedding,
        "source": "test/chunk",
        "date_ts": 0.0,
        "metadata": {}
    }]

    _export_vectors_to_sqlite(mock_vector_store, db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT embedding FROM chunks")
    blob = cursor.fetchone()[0]

    # Unpack blob as floats
    floats = struct.unpack(f"{len(blob)//4}f", blob)
    assert len(floats) == 384
    assert floats[0] == pytest.approx(0.5)
    assert floats[1] == pytest.approx(0.3)
    assert floats[2] == pytest.approx(0.8)

    conn.close()
