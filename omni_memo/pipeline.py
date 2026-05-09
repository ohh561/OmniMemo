"""End-to-end meeting processing pipeline."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from omni_memo.config import AppConfig
from omni_memo.omni.processor import OmniProcessor, ProcessingResult
from omni_memo.pro.analyzer import ProAnalyzer
from omni_memo.tts.generator import TTSGenerator
from omni_memo.agent.dispatcher import AgentDispatcher
from omni_memo.utils.formatter import MeetingMinutes
from omni_memo.utils.chunker import estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Full pipeline output."""

    minutes: MeetingMinutes
    omni_result: ProcessingResult
    meeting_type: dict
    voice_script: str = ""
    voice_path: str = ""
    total_tokens: int = 0


class MeetingPipeline:
    """Full meeting processing pipeline: input → Omni → Pro → TTS."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.omni = OmniProcessor(config.mimo)
        self.pro = ProAnalyzer(config.mimo)
        self.tts = TTSGenerator(config.mimo)
        self.agent = AgentDispatcher(config.mimo)

    def process_text(
        self,
        text: str,
        title: str = "",
        generate_voice: bool = False,
    ) -> PipelineResult:
        """Process meeting text through the full pipeline.

        Args:
            text: Meeting transcript text.
            title: Optional meeting title.
            generate_voice: Whether to generate TTS summary.

        Returns:
            PipelineResult with all outputs.
        """
        lang = self.config.language
        total_tokens = 0

        # Step 1: Classify meeting type
        logger.info("Step 1/4: Classifying meeting type...")
        excerpt = text[:2000]
        meeting_type = self.agent.classify(excerpt, lang)
        logger.info("Meeting type: %s (confidence: %.2f)",
                    meeting_type.get("type", "unknown"),
                    meeting_type.get("confidence", 0))

        # Step 2: Omni multimodal processing
        logger.info("Step 2/4: Processing with MiMo-Omni...")
        omni_result = self.omni.process_text(text, lang)
        total_tokens += omni_result.token_usage
        logger.info("Extracted %d segments (%d chunks, %s full context)",
                    omni_result.total_segments, omni_result.chunks_processed,
                    "used" if omni_result.used_full_context else "no")

        # Step 3: Pro deep analysis
        logger.info("Step 3/4: Analyzing with MiMo-Pro...")
        template = self.agent.get_template(meeting_type.get("type", "general"), lang)
        minutes = self.pro.analyze(omni_result.segments, lang)
        if title:
            minutes.title = title
        total_tokens += minutes.processing_stats.get("pro_token_usage", 0)

        # Step 4: Optional TTS
        voice_script = ""
        voice_path = ""
        if generate_voice:
            logger.info("Step 4/4: Generating voice summary...")
            output_dir = self.config.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            audio_path = output_dir / "summary.mp3"
            voice_script, voice_path = self.tts.generate_summary_audio(
                minutes, audio_path, lang,
            )
        else:
            logger.info("Step 4/4: Skipping TTS (not requested)")

        # Populate processing stats
        minutes.processing_stats.update({
            "meeting_type": meeting_type,
            "omni_chunks": omni_result.chunks_processed,
            "omni_segments": omni_result.total_segments,
            "used_full_context": omni_result.used_full_context,
            "total_tokens": total_tokens,
        })

        return PipelineResult(
            minutes=minutes,
            omni_result=omni_result,
            meeting_type=meeting_type,
            voice_script=voice_script,
            voice_path=str(voice_path),
            total_tokens=total_tokens,
        )

    def process_file(
        self,
        file_path: str,
        title: str = "",
        generate_voice: bool = False,
    ) -> PipelineResult:
        """Process a meeting transcript file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = path.read_text(encoding="utf-8")
        if not title:
            title = path.stem

        logger.info("Processing %s: %d chars, ~%d tokens",
                    path.name, len(text), estimate_tokens(text))
        return self.process_text(text, title, generate_voice)

    def save_results(self, result: PipelineResult, output_dir: str | Path | None = None):
        """Save all pipeline outputs to files."""
        out = Path(output_dir) if output_dir else self.config.output_dir
        out.mkdir(parents=True, exist_ok=True)

        # Markdown minutes
        md_path = out / "minutes.md"
        md_path.write_text(result.minutes.to_markdown(), encoding="utf-8")
        logger.info("Saved: %s", md_path)

        # JSON minutes
        json_path = out / "minutes.json"
        json_path.write_text(result.minutes.to_json(), encoding="utf-8")
        logger.info("Saved: %s", json_path)

        # Omni raw segments
        segments_path = out / "segments.json"
        segments_path.write_text(
            json.dumps(result.omni_result.segments, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Saved: %s", segments_path)

        # Voice script
        if result.voice_script:
            script_path = out / "voice_script.txt"
            script_path.write_text(result.voice_script, encoding="utf-8")
            logger.info("Saved: %s", script_path)
