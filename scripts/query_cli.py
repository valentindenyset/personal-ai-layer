"""Interactive CLI to test retrieval against the stores."""
import logging
import warnings
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from context.assembler import ContextAssembler
from retrieval import HybridRetrievalEngine
from stores.graph_store import GraphStore
from stores.vector_store import VectorStore
from scripts.export_cli import app as export_app

app = typer.Typer()
console = Console()
logging.basicConfig(level=logging.WARNING)

# Add export subcommand
app.add_typer(export_app, name="export-ios")


@app.command()
def query(
    q: str = typer.Argument(..., help="Your question"),
    top_k: int = typer.Option(10, help="Number of chunks to retrieve"),
    source: str = typer.Option("", help="Filter by source (e.g. gmail, calendar)"),
):
    """Query the personal memory layer."""
    vs = VectorStore()
    gs = GraphStore()
    engine = HybridRetrievalEngine(vs, gs)
    assembler = ContextAssembler()

    filters = {"source": source} if source else None
    chunks = engine.retrieve(q, top_k=top_k, filters=filters)
    context = assembler.assemble(chunks, q)

    console.print(Panel(Text(context), title=f"[bold cyan]Query:[/] {q}", border_style="cyan"))
    console.print(f"\n[dim]Retrieved {len(chunks)} chunks[/dim]")


@app.command()
def chat():
    """Interactive chat loop with Claude using your memory as context."""
    import anthropic
    from pathlib import Path
    from config.settings import settings

    system = Path("agent/prompts/system.md").read_text()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    vs = VectorStore()
    gs = GraphStore()
    engine = HybridRetrievalEngine(vs, gs)
    assembler = ContextAssembler()
    history = []

    console.print("[bold green]Personal AI — type 'exit' to quit[/]")
    while True:
        user_input = console.input("[bold]You:[/] ")
        if user_input.strip().lower() in {"exit", "quit"}:
            break

        chunks = engine.retrieve(user_input)
        context = assembler.assemble(chunks, user_input)
        augmented = f"{context}\n\nUser question: {user_input}"

        history.append({"role": "user", "content": augmented})
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=2048,
            system=system,
            messages=history,
        )
        answer = response.content[0].text
        history.append({"role": "assistant", "content": answer})
        console.print(f"[bold cyan]AI:[/] {answer}\n")


if __name__ == "__main__":
    app()
