"""Tests for text chunking utilities."""

import pytest
from omni_memo.utils.chunker import (
    estimate_tokens,
    chunk_text,
    should_use_full_context,
    TextChunk,
)


class TestEstimateTokens:
    """Token estimation tests."""

    def test_empty_text(self):
        assert estimate_tokens("") == 0

    def test_ascii_text(self):
        tokens = estimate_tokens("hello world")
        assert tokens > 0
        assert tokens < 10

    def test_chinese_text(self):
        tokens = estimate_tokens("你好世界")
        # CJK chars ~1.5 tokens each
        assert tokens >= 4

    def test_mixed_text(self):
        tokens = estimate_tokens("Hello 你好 World 世界")
        assert tokens > 0


class TestChunkText:
    """Text chunking tests."""

    def test_empty_text(self):
        assert chunk_text("") == []

    def test_short_text_single_chunk(self):
        text = "这是一段简短的文本。" * 10
        chunks = chunk_text(text, max_tokens=10000)
        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].text == text

    def test_long_text_multiple_chunks(self):
        # Generate text with paragraph breaks for proper chunking
        text = "\n\n".join(["这是一段用于测试的会议记录内容。" * 100 for _ in range(50)])
        chunks = chunk_text(text, max_tokens=50000)
        assert len(chunks) > 1
        # Verify all chunks are indexed
        for i, c in enumerate(chunks):
            assert c.index == i

    def test_chunk_metadata(self):
        text = "段落一。" * 100 + "\n\n" + "段落二。" * 100
        chunks = chunk_text(text, max_tokens=1000)
        for c in chunks:
            assert isinstance(c, TextChunk)
            assert c.char_start >= 0
            assert c.char_end > c.char_start
            assert c.token_estimate > 0

    def test_respect_paragraphs(self):
        text = "\n\n".join([f"段落{i}。" * 200 for i in range(20)])
        chunks = chunk_text(text, max_tokens=2000, respect_paragraphs=True)
        assert len(chunks) >= 2

    def test_overlap(self):
        text = "内容A。" * 2000 + "\n\n" + "内容B。" * 2000
        chunks = chunk_text(text, max_tokens=5000, overlap_tokens=500)
        # With overlap, we should have more chunks than without
        chunks_no_overlap = chunk_text(text, max_tokens=5000, overlap_tokens=0)
        assert len(chunks) >= len(chunks_no_overlap)


class TestShouldUseFullContext:
    """Full context detection tests."""

    def test_short_text(self):
        assert should_use_full_context("短文本") is False

    def test_threshold(self):
        # Just below threshold
        short = "x" * 100
        assert should_use_full_context(short, threshold=100000) is False

    def test_above_threshold(self):
        # Generate text above threshold
        long_text = "这是长文本内容。" * 100000
        assert should_use_full_context(long_text, threshold=10000) is True
