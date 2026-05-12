from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # Vector store
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "personal_memory"

    # Graph store
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    # Embeddings
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_token_path: Path = Path(".secrets/google_token.json")

    # Microsoft
    ms_client_id: str = ""
    ms_tenant_id: str = ""
    ms_client_secret: str = ""

    # Sync
    sync_interval_hours: int = 6
    gdpr_exports_dir: Path = Path("./data/gdpr_exports")

    # MCP server
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8765


settings = Settings()
