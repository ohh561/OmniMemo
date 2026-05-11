"""Tests for configuration management."""

import os
import pytest
from omni_memo.config import MiMoConfig, AppConfig


class TestMiMoConfig:
    """MiMoConfig tests."""

    def test_default_values(self):
        config = MiMoConfig()
        assert config.api_base == "https://api.xiaomimimo.com/v1"
        assert config.model_omni == "mimo-v2.5-omni"
        assert config.model_pro == "mimo-v2.5-pro"
        assert config.model_tts == "mimo-v2.5-tts"
        assert config.max_context_tokens == 1_000_000

    def test_validate_missing_key(self):
        config = MiMoConfig(api_key="")
        issues = config.validate()
        assert len(issues) == 1
        assert "MIMO_API_KEY" in issues[0]

    def test_validate_with_key(self):
        config = MiMoConfig(api_key="test-key")
        assert config.validate() == []


class TestAppConfig:
    """AppConfig tests."""

    def test_default_config(self):
        config = AppConfig()
        assert config.language == "zh"
        assert config.verbose is False
        assert config.mimo.max_context_tokens == 1_000_000

    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key-123")
        monkeypatch.setenv("MIMO_MODEL_PRO", "custom-model")
        monkeypatch.setenv("OMNIMEMO_LANG", "en")
        config = AppConfig.load()
        assert config.mimo.api_key == "test-key-123"
        assert config.mimo.model_pro == "custom-model"
        assert config.language == "en"
