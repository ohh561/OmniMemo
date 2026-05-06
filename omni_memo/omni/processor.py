"""MiMo-Omni multimodal processor — unified audio/video/image/text understanding."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from omni_memo.config import MiMoConfig
from omni_memo.utils.chunker import estimate_tokens, chunk_text, should_use_full_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_ZH = """你是 OmniMemo 的多模态理解引擎。你的任务是理解会议的原始素材（录音转写文本、截图描述、视频帧描述），并输出结构化的会议内容理解结果。

对于输入内容，请提取：
1. 发言人识别（如有线索）
2. 每段内容的核心议题
3. 关键数据/图表引用（如有）
4. 时间线标记（如有）

输出 JSON 格式：
{
  "segments": [
    {
      "speaker": "发言人",
      "content": "核心内容",
      "topic_tags": ["标签"],
      "references": ["引用的数据/图表"],
      "timestamp_hint": "时间线索"
    }
  ],
  "detected_language": "zh/en/mixed",
  "total_segments": N
}"""

SYSTEM_PROMPT_EN = """You are OmniMemo's multimodal understanding engine. Extract structured content from meeting materials (transcripts, screenshot descriptions, video frame descriptions).

Output JSON:
{
  "segments": [
    {
      "speaker": "speaker name",
      "content": "core content",
      "topic_tags": ["tags"],
      "references": ["data/chart references"],
      "timestamp_hint": "time clue"
    }
  ],
  "detected_language": "zh/en/mixed",
  "total_segments": N
}"""


@dataclass
class ProcessingResult:
    """Result from Omni processing."""

    segments: list[dict]
    detected_language: str
    total_segments: int
    token_usage: int
    chunks_processed: int
    used_full_context: bool


class OmniProcessor:
    """Process multimodal meeting inputs via MiMo-Omni."""

    def __init__(self, config: MiMoConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def process_text(self, text: str, language: str = "zh") -> ProcessingResult:
        """Process meeting transcript text.

        For short texts (< 100K tokens), send as single request.
        For long texts, leverage MiMo's 1M context window to process in fewer chunks.
        """
        sys_prompt = SYSTEM_PROMPT_ZH if language == "zh" else SYSTEM_PROMPT_EN
        total_tokens = estimate_tokens(text)
        use_full = should_use_full_context(text)

        if use_full:
            # Use larger chunk size to leverage 1M context window
            max_chunk = self.config.max_context_tokens - 10_000  # leave room for system + output
            chunks = chunk_text(text, max_tokens=max_chunk, overlap_tokens=5_000)
        else:
            chunks = chunk_text(text, max_tokens=400_000, overlap_tokens=2_000)

        all_segments = []
        total_usage = 0

        for chunk in chunks:
            logger.info("Processing chunk %d/%d (%d tokens)",
                       chunk.index + 1, len(chunks), chunk.token_estimate)

            response = self.client.chat.completions.create(
                model=self.config.model_omni,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": chunk.text},
                ],
                max_tokens=self.config.max_output_tokens,
                temperature=self.config.temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            total_usage += response.usage.total_tokens if response.usage else 0

            try:
                parsed = json.loads(content)
                segments = parsed.get("segments", [])
                all_segments.extend(segments)
            except json.JSONDecodeError:
                logger.warning("Failed to parse Omni response for chunk %d", chunk.index)

        # Deduplicate segments from overlapping chunks
        deduped = self._deduplicate_segments(all_segments)

        return ProcessingResult(
            segments=deduped,
            detected_language=language,
            total_segments=len(deduped),
            token_usage=total_usage,
            chunks_processed=len(chunks),
            used_full_context=use_full,
        )

    def process_file(self, file_path: str, language: str = "zh") -> ProcessingResult:
        """Process a text file containing meeting transcript."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = path.read_text(encoding="utf-8")
        logger.info("Loaded %s: %d chars, ~%d tokens",
                    path.name, len(text), estimate_tokens(text))
        return self.process_text(text, language)

    def _deduplicate_segments(self, segments: list[dict]) -> list[dict]:
        """Remove duplicate segments from overlapping chunks."""
        seen = set()
        result = []
        for seg in segments:
            key = (seg.get("speaker", ""), seg.get("content", "")[:100])
            if key not in seen:
                seen.add(key)
                result.append(seg)
        return result
