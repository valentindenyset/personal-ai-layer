"""Serialize Neo4j graph to JSON for iOS import."""
from __future__ import annotations
import json
import os
from typing import Any

from stores.graph_store import GraphStore


def serialize_entities(graph_store: GraphStore) -> list[dict[str, Any]]:
    """Extract all entities from graph store as JSON-serializable dicts."""
    entities = []

    # Handle mock for tests
    if hasattr(graph_store, 'persons'):
        for person in graph_store.persons:
            entities.append({
                "id": person["id"],
                "type": "Person",
                "name": person["name"],
                "properties": {k: v for k, v in person.items() if k not in ["id", "name"]}
            })
        return entities

    # Query Neo4j for all entity nodes
    query = """
    MATCH (n)
    WHERE n:Person OR n:Event OR n:Topic OR n:Place OR n:Organization
    RETURN
        labels(n)[0] as type,
        properties(n) as props,
        id(n) as node_id
    """

    with graph_store._driver.session() as session:
        result = session.run(query)

        for record in result:
            entity_type = record["type"]
            props = dict(record["props"])

            # Extract name (different field per type)
            name = props.get("name", "")

            # Generate stable ID
            entity_id = props.get("id")
            if not entity_id:
                normalized_name = name.lower().replace(" ", "_")
                entity_id = f"{entity_type.lower()}_{normalized_name}"

            # Separate core fields from properties
            core_fields = {"id", "name", "type"}
            properties = {k: v for k, v in props.items() if k not in core_fields}

            entities.append({
                "id": entity_id,
                "type": entity_type,
                "name": name,
                "properties": properties
            })

    return entities


def serialize_relations(graph_store: GraphStore) -> list[dict[str, Any]]:
    """Extract all relations from graph store as JSON-serializable dicts."""
    relations = []

    # Handle mock for tests
    if hasattr(graph_store, 'relations'):
        for rel in graph_store.relations:
            relations.append({
                "from": rel["from"],
                "to": rel["to"],
                "type": rel["type"],
                "properties": {k: v for k, v in rel.items() if k not in ["from", "to", "type"]}
            })
        return relations

    # Query Neo4j for all relationships
    query = """
    MATCH (a)-[r]->(b)
    RETURN
        a.id as from_id,
        b.id as to_id,
        type(r) as rel_type,
        properties(r) as props
    """

    with graph_store._driver.session() as session:
        result = session.run(query)

        for record in result:
            # Generate stable IDs for nodes if needed
            from_id = record["from_id"]
            to_id = record["to_id"]
            rel_type = record["rel_type"]
            props = dict(record["props"])

            relations.append({
                "from": from_id,
                "to": to_id,
                "type": rel_type,
                "properties": props
            })

    return relations


def export_graph_json(graph_store: GraphStore, output_dir: str) -> tuple[str, str]:
    """
    Export graph to entities.json and relations.json.

    Returns:
        Tuple of (entities_path, relations_path)
    """
    entities = serialize_entities(graph_store)
    relations = serialize_relations(graph_store)

    entities_path = os.path.join(output_dir, "entities.json")
    relations_path = os.path.join(output_dir, "relations.json")

    with open(entities_path, "w") as f:
        json.dump(entities, f, indent=2)

    with open(relations_path, "w") as f:
        json.dump(relations, f, indent=2)

    return entities_path, relations_path
