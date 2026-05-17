"""Tests for graph serializer functionality."""
import pytest
import json
from exports.graph_serializer import serialize_entities, serialize_relations


def test_serialize_entities_extracts_person_nodes(mock_graph_store):
    """Test that person entities are serialized correctly."""
    # Setup mock graph with person nodes
    mock_graph_store.persons = [
        {
            "id": "person_alexandre",
            "name": "Alexandre Guedj",
            "phone_numbers": ["+33612345678"],
            "emails": ["alex@test.com"],
            "company": "Test Corp",
            "mentions_count": 10
        }
    ]

    entities = serialize_entities(mock_graph_store)

    assert len(entities) == 1
    assert entities[0]["id"] == "person_alexandre"
    assert entities[0]["type"] == "Person"
    assert entities[0]["name"] == "Alexandre Guedj"
    assert entities[0]["properties"]["phone_numbers"] == ["+33612345678"]


def test_serialize_relations_extracts_edges(mock_graph_store):
    """Test that relations are serialized correctly."""
    mock_graph_store.relations = [
        {
            "from": "person_alex",
            "to": "person_marie",
            "type": "KNOWS",
            "strength": 5,
            "since_ts": 1640995200.0
        }
    ]

    relations = serialize_relations(mock_graph_store)

    assert len(relations) == 1
    assert relations[0]["from"] == "person_alex"
    assert relations[0]["to"] == "person_marie"
    assert relations[0]["type"] == "KNOWS"
    assert relations[0]["properties"]["strength"] == 5
