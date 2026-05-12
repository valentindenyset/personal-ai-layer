"""Initialize Qdrant collection and Neo4j constraints."""
import logging

from stores.graph_store import GraphStore
from stores.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("setting up vector store …")
    vs = VectorStore()
    vs.ensure_collection()

    logger.info("setting up graph store …")
    gs = GraphStore()
    gs.ensure_constraints()
    gs.close()

    logger.info("stores ready.")


if __name__ == "__main__":
    main()
