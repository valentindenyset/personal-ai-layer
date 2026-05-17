"""Pytest fixtures for testing."""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for testing."""
    mock = MagicMock()
    mock.chunks = []
    mock._client = MagicMock()
    mock._collection = "test_collection"
    return mock


@pytest.fixture
def mock_graph_store():
    """Mock GraphStore for testing."""
    mock = MagicMock()
    mock.persons = []
    mock.relations = []
    return mock
