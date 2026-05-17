"""Serialize Neo4j graph to JSON for iOS import."""
from __future__ import annotations
import json
from typing import Any


def serialize_entities(graph_store) -> list[dict[str, Any]]:
    """Extract all entities from graph store as JSON-serializable dicts."""
    return []  # Will implement in next task


def serialize_relations(graph_store) -> list[dict[str, Any]]:
    """Extract all relations from graph store as JSON-serializable dicts."""
    return []  # Will implement in next task


def export_graph_json(graph_store, output_dir: str) -> tuple[str, str]:
    """
    Export graph to entities.json and relations.json.

    Returns:
        Tuple of (entities_path, relations_path)
    """
    import os

    entities = serialize_entities(graph_store)
    relations = serialize_relations(graph_store)

    entities_path = os.path.join(output_dir, "entities.json")
    relations_path = os.path.join(output_dir, "relations.json")

    with open(entities_path, "w") as f:
        json.dump(entities, f, indent=2)

    with open(relations_path, "w") as f:
        json.dump(relations, f, indent=2)

    return entities_path, relations_path
