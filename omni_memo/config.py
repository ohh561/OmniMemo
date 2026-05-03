"""Configuration management for OmniMemo."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class MiMoConfig:
    """MiMo API configuration."""

    api_key: str = ""
    api_base: str = "https://api.xiaomimimo.com/v1"
    model_omni: str = "mimo-v2.5-omni"
    model_pro: str = "mimo-v2.5-pro"
    model_tts: str = "mimo-v2.5-tts"
    max_context_tokens: int = 1_000_000  # MiMo 1M context window
    max_output_tokens: int = 32_768
    temperature: float = 0.3

    def validate(self) -> list[str]:
        """Return list of missing required fields."""
        issues = []
        if not self.api_key:
            issues.append("MIMO_API_KEY not set")
        return issues


@dataclass
class AppConfig:
    """Application configuration."""

    mimo: MiMoConfig = field(default_factory=MiMoConfig)
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    language: str = "zh"  # zh | en
    verbose: bool = False

    @classmethod
    def load(cls, env_file: str | None = None) -> "AppConfig":
        """Load config from environment and .env file."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        mimo = MiMoConfig(
            api_key=os.getenv("MIMO_API_KEY", ""),
            api_base=os.getenv("MIMO_API_BASE", "https://api.xiaomimimo.com/v1"),
            model_omni=os.getenv("MIMO_MODEL_OMNI", "mimo-v2.5-omni"),
            model_pro=os.getenv("MIMO_MODEL_PRO", "mimo-v2.5-pro"),
            model_tts=os.getenv("MIMO_MODEL_TTS", "mimo-v2.5-tts"),
            max_context_tokens=int(os.getenv("MIMO_MAX_CONTEXT", "1000000")),
            max_output_tokens=int(os.getenv("MIMO_MAX_OUTPUT", "32768")),
            temperature=float(os.getenv("MIMO_TEMPERATURE", "0.3")),
        )

        output_dir = Path(os.getenv("OMNIMEMO_OUTPUT_DIR", "./output"))

        return cls(
            mimo=mimo,
            output_dir=output_dir,
            language=os.getenv("OMNIMEMO_LANG", "zh"),
            verbose=os.getenv("OMNIMEMO_VERBOSE", "").lower() in ("1", "true", "yes"),
        )
