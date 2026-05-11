"""Tests for the meeting processing pipeline (with mocked API)."""

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from omni_memo.config import AppConfig, MiMoConfig
from omni_memo.pipeline import MeetingPipeline


@pytest.fixture
def mock_config():
    """Config with fake API key."""
    return AppConfig(
        mimo=MiMoConfig(api_key="test-key-fake"),
        language="zh",
    )


class TestPipelineIntegration:
    """Pipeline integration tests with mocked API calls."""

    def test_pipeline_initialization(self, mock_config):
        pipeline = MeetingPipeline(mock_config)
        assert pipeline.omni is not None
        assert pipeline.pro is not None
        assert pipeline.tts is not None
        assert pipeline.agent is not None

    @patch("omni_memo.omni.processor.OpenAI")
    @patch("omni_memo.pro.analyzer.OpenAI")
    @patch("omni_memo.agent.dispatcher.OpenAI")
    def test_process_text_flow(self, mock_agent_openai, mock_pro_openai, mock_omni_openai, mock_config):
        """Test the full pipeline flow with mocked API responses."""
        # Mock Omni response
        omni_client = MagicMock()
        mock_omni_openai.return_value = omni_client
        omni_response = MagicMock()
        omni_response.choices = [MagicMock()]
        omni_response.choices[0].message.content = json.dumps({
            "segments": [
                {"speaker": "张三", "content": "讨论Q2目标", "topic_tags": ["规划"], "references": [], "timestamp_hint": ""},
                {"speaker": "李四", "content": "同意方案A", "topic_tags": ["决策"], "references": [], "timestamp_hint": ""},
            ],
            "detected_language": "zh",
            "total_segments": 2,
        })
        omni_response.usage = MagicMock()
        omni_response.usage.total_tokens = 5000
        omni_client.chat.completions.create.return_value = omni_response

        # Mock Agent response
        agent_client = MagicMock()
        mock_agent_openai.return_value = agent_client
        agent_response = MagicMock()
        agent_response.choices = [MagicMock()]
        agent_response.choices[0].message.content = json.dumps({
            "type": "weekly",
            "confidence": 0.9,
            "reason": "周会讨论",
        })
        agent_response.usage = MagicMock()
        agent_response.usage.total_tokens = 200
        agent_client.chat.completions.create.return_value = agent_response

        # Mock Pro response
        pro_client = MagicMock()
        mock_pro_openai.return_value = pro_client
        pro_response = MagicMock()
        pro_response.choices = [MagicMock()]
        pro_response.choices[0].message.content = json.dumps({
            "title": "周会",
            "summary": "讨论了Q2目标",
            "participants": ["张三", "李四"],
            "topics": [{"title": "Q2目标", "content": "达成共识"}],
            "decisions": [{"topic": "方案", "decision": "采用方案A", "rationale": "成本低"}],
            "action_items": [{"owner": "张三", "task": "写方案", "deadline": "下周五", "priority": "high"}],
            "disputes": [],
        })
        pro_response.usage = MagicMock()
        pro_response.usage.total_tokens = 3000
        pro_client.chat.completions.create.return_value = pro_response

        # Run pipeline
        pipeline = MeetingPipeline(mock_config)
        result = pipeline.process_text("张三：我们来讨论Q2目标。李四：我同意方案A。")

        # Verify results
        assert result.minutes.title == "周会"
        assert len(result.minutes.decisions) == 1
        assert len(result.minutes.action_items) == 1
        assert result.omni_result.total_segments == 2
        assert result.meeting_type.get("type") == "weekly"
        assert result.total_tokens > 0
