"""Neo4j graph store wrapper."""
from __future__ import annotations

import logging

from neo4j import GraphDatabase

from config.settings import settings

logger = logging.getLogger(__name__)


class GraphStore:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        self._driver.close()

    def ensure_constraints(self):
        with self._driver.session() as s:
            for label in ["Person", "Organization", "Place", "Event", "Concept"]:
                s.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE")
        logger.info("graph store constraints ready")

    def upsert_entities_from_chunks(self, chunks, doc) -> None:
        """Create entity nodes and link them to their source document."""
        with self._driver.session() as session:
            # Upsert the document node
            session.run(
                "MERGE (d:Document {id: $id}) SET d.source = $source, d.created_at = $ts",
                id=doc.doc_id,
                source=doc.source,
                ts=doc.created_at.isoformat(),
            )
            for chunk in chunks:
                for entity in chunk.entities:
                    session.run(
                        """
                        MERGE (e:Entity {name: $name, type: $type})
                        WITH e
                        MATCH (d:Document {id: $doc_id})
                        MERGE (d)-[:MENTIONS]->(e)
                        """,
                        name=entity["name"],
                        type=entity["type"],
                        doc_id=doc.doc_id,
                    )

    def find_related_entities(self, entity_names: list[str], depth: int = 2) -> list[dict]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity)-[r*1..$depth]-(related)
                WHERE e.name IN $names
                RETURN DISTINCT related.name AS name, related.type AS type,
                       labels(related) AS labels
                LIMIT 50
                """,
                names=entity_names,
                depth=depth,
            )
            return [dict(r) for r in result]

    def get_entity_documents(self, entity_name: str) -> list[str]:
        with self._driver.session() as session:
            result = session.run(
                "MATCH (d:Document)-[:MENTIONS]->(e:Entity {name: $name}) RETURN d.id AS doc_id",
                name=entity_name,
            )
            return [r["doc_id"] for r in result]
