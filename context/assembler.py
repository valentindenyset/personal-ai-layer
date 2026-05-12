"""Formats retrieved chunks into an LLM-ready context string."""
from __future__ import annotations

import tiktoken

from .budget import TokenBudget


class ContextAssembler:
    ENCODING = "cl100k_base"

    def __init__(self, max_tokens: int = 8000):
        self.budget = TokenBudget(max_tokens)
        self._enc = tiktoken.get_encoding(self.ENCODING)

    def assemble(self, chunks, query: str) -> str:
        """Return a formatted context block that fits within the token budget."""
        sections: list[str] = []
        used = self._count(f"Query: {query}\n\nContext:\n")

        for i, chunk in enumerate(chunks):
            source_label = chunk.source.replace("_", " ").title()
            block = f"[{i+1}] ({source_label})\n{chunk.text}\n"
            tokens = self._count(block)
            if not self.budget.fits(used, tokens):
                break
            sections.append(block)
            used += tokens

        if not sections:
            return "No relevant context found."

        return "Context:\n\n" + "\n".join(sections)

    def _count(self, text: str) -> int:
        return len(self._enc.encode(text))
