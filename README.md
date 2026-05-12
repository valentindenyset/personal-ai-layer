# Personal AI Layer

A personal memory layer that indexes all your data (Calendar, Mail, Health, Messages, Notes, Photos, WhatsApp…) into a **vector store** (Qdrant) + **graph store** (Neo4j), then exposes everything via an **MCP server** so any Claude agent can query your life.

## Architecture

```
Data sources
  Calendar · Mail · Health · Photos · Contacts
  iMessage (macOS) · Notes (macOS)
  GDPR exports: WhatsApp · Instagram
         │
         ▼
  Ingestion pipeline
  Chunk → Embed (sentence-transformers) → Extract entities (spaCy) → Deduplicate
         │                    │
         ▼                    ▼
  Vector store          Graph store
  (Qdrant)              (Neo4j)
  Semantic search       Person · Event · Place · Concept
         │                    │
         └──────┬─────────────┘
                ▼
  Hybrid retrieval engine
  Vector similarity + graph traversal → RRF fusion → cross-encoder rerank
                ▼
  Context assembler  (token budget management)
                ▼
  MCP server  →  any Claude agent via context(query, topK, filters)
```

## Quick start

### 1. Infrastructure

```bash
docker compose up -d          # starts Qdrant :6333 and Neo4j :7687
```

### 2. Python environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# NLP models
python -m spacy download fr_core_news_lg
```

### 3. Configure

```bash
cp .env.example .env          # fill in your API keys
# edit config/sources.yaml to enable/disable sources
```

### 4. Initialize stores

```bash
python scripts/setup_stores.py
```

### 5. Ingest your data

**APIs (Calendar, Gmail):**
```bash
python -c "from sync.jobs.full_sync import run_full_sync; run_full_sync()"
```

**Apple Health export:**
```
Health app → Profile photo → Export All Health Data → unzip to data/apple_health_export/
```

**Apple Notes (macOS):**
```bash
osascript scripts/export_notes.applescript
```

**iMessage (macOS — requires Full Disk Access for Terminal):**
Enabled automatically if `macos_imessage.enabled: true` in `config/sources.yaml`.

**WhatsApp GDPR export:**
```bash
# Place unzipped export at data/gdpr_exports/whatsapp/
python scripts/ingest_gdpr.py whatsapp data/gdpr_exports/whatsapp
```

### 6. Query

```bash
pai "Who did I meet in January 2024?"            # single query
pai chat                                          # interactive chat with Claude
```

### 7. MCP server (for Claude Desktop / other agents)

```bash
python agent/mcp_server.py
```

Add to your Claude Desktop `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "personal-memory": {
      "command": "python",
      "args": ["/path/to/personal-ai-layer/agent/mcp_server.py"]
    }
  }
}
```

### 8. Background sync

```bash
python sync/scheduler.py      # syncs every N hours (SYNC_INTERVAL_HOURS in .env)
```

## Project structure

```
personal-ai-layer/
├── config/               Settings + source configuration
├── ingestion/            Pipeline: chunk → embed → extract → dedup
│   └── sources/          One module per data source
│       ├── gdpr_exports/ WhatsApp, Instagram parsers
│       └── macos/        iMessage, Notes (macOS)
├── stores/
│   ├── vector_store/     Qdrant client wrapper
│   └── graph_store/      Neo4j client wrapper
├── retrieval/            Hybrid engine: fusion + reranking
├── context/              Token-budget-aware context assembler
├── agent/
│   ├── mcp_server.py     MCP endpoint
│   ├── tools/            Stage 2 action tools (calendar, mail)
│   └── prompts/          System prompt
├── sync/                 APScheduler sync daemon
└── scripts/              CLI tools + AppleScript export helper
```

## Roadmap

- **Stage 1 (current):** read-only memory queries via MCP
- **Stage 2:** write actions — create events, send emails, log health data
- **iOS shortcut:** trigger a sync from the iPhone Shortcuts app via a local HTTP endpoint
- **On-device embeddings:** CoreML model for fully offline operation
