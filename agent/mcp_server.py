"""MCP server exposing a `context` tool to any MCP-compatible agent."""
from __future__ import annotations

import logging

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from config.settings import settings
from context.assembler import ContextAssembler
from retrieval import HybridRetrievalEngine
from stores.graph_store import GraphStore
from stores.vector_store import VectorStore

logger = logging.getLogger(__name__)

server = Server("personal-ai-layer")
_engine: HybridRetrievalEngine | None = None
_assembler = ContextAssembler(max_tokens=8000)


def _get_engine() -> HybridRetrievalEngine:
    global _engine
    if _engine is None:
        vs = VectorStore()
        gs = GraphStore()
        _engine = HybridRetrievalEngine(vs, gs)
    return _engine


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="context",
            description=(
                "Retrieve relevant personal context for a query. "
                "Returns excerpts from the user's calendar, emails, messages, "
                "health data, notes, and social media exports."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query about the user's life or data",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of chunks to retrieve (default 10)",
                        "default": 10,
                    },
                    "source_filter": {
                        "type": "string",
                        "description": "Optional: filter to a specific source (e.g. 'gmail', 'calendar')",
                    },
                },
                "required": ["query"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "context":
        raise ValueError(f"unknown tool: {name}")

    query = arguments["query"]
    top_k = arguments.get("top_k", 10)
    source_filter = arguments.get("source_filter")
    filters = {"source": source_filter} if source_filter else None

    engine = _get_engine()
    chunks = engine.retrieve(query, top_k=top_k, filters=filters)
    context_text = _assembler.assemble(chunks, query)

    return [types.TextContent(type="text", text=context_text)]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
