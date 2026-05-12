"""Splits documents into overlapping chunks."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RawChunk:
    doc_id: str
    chunk_index: int
    text: str
    metadata: dict = field(default_factory=dict)


class Chunker:
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 64):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, doc) -> list[RawChunk]:
        """Split a Document into overlapping RawChunks."""
        sentences = self._split_sentences(doc.content)
        chunks: list[RawChunk] = []
        buffer: list[str] = []
        token_count = 0

        for sentence in sentences:
            sentence_tokens = len(sentence.split())
            if token_count + sentence_tokens > self.max_tokens and buffer:
                chunk_text = " ".join(buffer)
                chunks.append(RawChunk(
                    doc_id=doc.doc_id,
                    chunk_index=len(chunks),
                    text=chunk_text,
                    metadata={**doc.metadata, "source": doc.source},
                ))
                # Keep overlap
                overlap_sentences = self._trim_to_tokens(buffer, self.overlap_tokens)
                buffer = overlap_sentences
                token_count = sum(len(s.split()) for s in buffer)

            buffer.append(sentence)
            token_count += sentence_tokens

        if buffer:
            chunks.append(RawChunk(
                doc_id=doc.doc_id,
                chunk_index=len(chunks),
                text=" ".join(buffer),
                metadata={**doc.metadata, "source": doc.source},
            ))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    def _trim_to_tokens(self, sentences: list[str], max_tokens: int) -> list[str]:
        result: list[str] = []
        count = 0
        for s in reversed(sentences):
            t = len(s.split())
            if count + t > max_tokens:
                break
            result.insert(0, s)
            count += t
        return result
