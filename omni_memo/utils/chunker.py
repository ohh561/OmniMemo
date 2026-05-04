"""Long-text chunking strategies for context window management."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class TextChunk:
    """A chunk of text with position metadata."""

    index: int
    text: str
    char_start: int
    char_end: int
    token_estimate: int  # rough: 1 token ≈ 1.5 chars for Chinese, 4 chars for English


def estimate_tokens(text: str) -> int:
    """Rough token estimation: CJK chars count as ~1.5 tokens, ASCII as ~0.25."""
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    ascii_chars = len(text) - cjk
    return int(cjk * 1.5 + ascii_chars * 0.25)


def chunk_text(
    text: str,
    max_tokens: int = 800_000,
    overlap_tokens: int = 2_000,
    respect_paragraphs: bool = True,
) -> list[TextChunk]:
    """Split text into chunks that fit within a context window.

    Args:
        text: Input text to chunk.
        max_tokens: Maximum tokens per chunk.
        overlap_tokens: Token overlap between consecutive chunks.
        respect_paragraphs: Try to split at paragraph boundaries.

    Returns:
        List of TextChunk objects.
    """
    if not text.strip():
        return []

    total_tokens = estimate_tokens(text)

    # If it fits in one chunk, return as-is
    if total_tokens <= max_tokens:
        return [TextChunk(
            index=0, text=text, char_start=0, char_end=len(text),
            token_estimate=total_tokens,
        )]

    chunks: list[TextChunk] = []
    if respect_paragraphs:
        paragraphs = text.split("\n\n")
    else:
        # Split by sentences
        paragraphs = []
        for line in text.split("\n"):
            if line.strip():
                paragraphs.append(line)

    current_text = ""
    current_start = 0
    pos = 0
    chunk_idx = 0

    for para in paragraphs:
        para_with_sep = para + "\n\n" if respect_paragraphs else para + "\n"
        candidate = current_text + para_with_sep

        if estimate_tokens(candidate) > max_tokens and current_text:
            # Flush current chunk
            tok = estimate_tokens(current_text)
            chunks.append(TextChunk(
                index=chunk_idx, text=current_text.strip(),
                char_start=current_start, char_end=pos,
                token_estimate=tok,
            ))
            chunk_idx += 1

            # Overlap: keep last portion
            overlap_chars = int(overlap_tokens * 2)  # rough back-conversion
            if len(current_text) > overlap_chars:
                current_start = pos - overlap_chars
                current_text = current_text[-overlap_chars:] + para_with_sep
            else:
                current_start = pos
                current_text = para_with_sep
        else:
            if not current_text:
                current_start = pos
            current_text = candidate

        pos += len(para_with_sep)

    # Final chunk
    if current_text.strip():
        chunks.append(TextChunk(
            index=chunk_idx, text=current_text.strip(),
            char_start=current_start, char_end=len(text),
            token_estimate=estimate_tokens(current_text),
        ))

    return chunks


def should_use_full_context(text: str, threshold: int = 100_000) -> bool:
    """Determine if text is long enough to benefit from 1M context window."""
    return estimate_tokens(text) > threshold
