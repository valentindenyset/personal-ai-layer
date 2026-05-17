"""CLI for exporting data to iOS format."""
import typer
from pathlib import Path
from rich import print as rprint

from stores.vector_store import VectorStore
from stores.graph_store import GraphStore
from exports.ios_export import export_for_ios

app = typer.Typer(help="Export Personal AI data for iOS import")


@app.command()
def export(
    output: str = typer.Argument(..., help="Output path (without extension)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Export vector store and graph to iOS-compatible format."""
    rprint(f"[bold blue]Exporting to iOS format...[/bold blue]")
    rprint(f"Output: {output}")

    # Initialize stores
    vector_store = VectorStore()
    graph_store = GraphStore()

    # Export
    result = export_for_ios(vector_store, graph_store, output)

    # Print results
    rprint("[bold green]✓ Export complete![/bold green]")
    rprint(f"Database: {result['database']}")
    rprint(f"Entities: {result['entities']}")
    rprint(f"Relations: {result['relations']}")

    # Print stats
    if verbose:
        import sqlite3
        conn = sqlite3.connect(result["database"])
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        conn.close()

        import json
        with open(result["entities"]) as f:
            entity_count = len(json.load(f))
        with open(result["relations"]) as f:
            relation_count = len(json.load(f))

        rprint(f"\n[bold]Stats:[/bold]")
        rprint(f"  Chunks: {chunk_count:,}")
        rprint(f"  Entities: {entity_count:,}")
        rprint(f"  Relations: {relation_count:,}")


if __name__ == "__main__":
    app()
