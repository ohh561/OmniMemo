"""MiMo-TTS voice summary generator."""

from __future__ import annotations

import logging
from pathlib import Path

from openai import OpenAI

from omni_memo.config import MiMoConfig
from omni_memo.utils.formatter import MeetingMinutes

logger = logging.getLogger(__name__)

TTS_PROMPT_ZH = """请将以下会议纪要转化为自然流畅的语音摘要文本，控制在 3 分钟以内（约 600-800 字）。
要求：
1. 用口语化表达，适合通勤时收听
2. 重点突出决策和行动项
3. 保留关键数据和时间节点
4. 开头说明会议主题和参会人"""

TTS_PROMPT_EN = """Convert the following meeting minutes into a natural spoken summary, 2-3 minutes max.
Focus on decisions and action items. Use conversational tone."""


class TTSGenerator:
    """Generate voice summaries via MiMo-TTS."""

    def __init__(self, config: MiMoConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def generate_script(self, minutes: MeetingMinutes, language: str = "zh") -> str:
        """Generate a TTS-ready script from meeting minutes."""
        prompt = TTS_PROMPT_ZH if language == "zh" else TTS_PROMPT_EN
        minutes_text = minutes.to_markdown()

        response = self.client.chat.completions.create(
            model=self.config.model_pro,  # Use Pro to write the script
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": minutes_text},
            ],
            max_tokens=4096,
            temperature=0.5,
        )

        return response.choices[0].message.content or ""

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        """Synthesize text to audio via MiMo-TTS.

        Args:
            text: Text to synthesize (max ~5000 chars per call).
            output_path: Path to save the audio file.

        Returns:
            Path to the generated audio file.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Synthesizing %d chars to %s", len(text), output)

        response = self.client.audio.speech.create(
            model=self.config.model_tts,
            input=text[:5000],  # TTS input limit
            voice="alloy",
            response_format="mp3",
        )

        response.stream_to_file(str(output))
        logger.info("Audio saved to %s", output)
        return output

    def generate_summary_audio(
        self,
        minutes: MeetingMinutes,
        output_path: str | Path,
        language: str = "zh",
    ) -> tuple[str, Path]:
        """Full pipeline: minutes → script → audio.

        Returns:
            Tuple of (script_text, audio_path).
        """
        script = self.generate_script(minutes, language)
        audio_path = self.synthesize(script, output_path)
        return script, audio_path
