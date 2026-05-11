"""Tests for output formatting."""

import json
import pytest
from omni_memo.utils.formatter import (
    MeetingMinutes, Decision, ActionItem, Dispute,
)


@pytest.fixture
def sample_minutes():
    """Create a sample MeetingMinutes for testing."""
    return MeetingMinutes(
        title="Q2 产品规划会",
        date="2026-05-15",
        duration_estimate="1h30m",
        participants=["张三", "李四", "王五"],
        summary="讨论了 Q2 产品路线图，确定了三个核心功能的优先级。",
        topics=[
            {"title": "用户增长", "content": "DAU 目标 50 万，需优化新用户引导流程"},
            {"title": "技术债务", "content": "重构支付模块，预计 2 周"},
        ],
        decisions=[
            Decision(
                topic="支付模块重构",
                decision="采用微服务架构拆分支付模块",
                rationale="当前单体架构扩展性差，Q3 预计接入 3 个新支付渠道",
            ),
        ],
        action_items=[
            ActionItem(owner="张三", task="完成支付模块技术方案", deadline="2026-05-22", priority="high"),
            ActionItem(owner="李四", task="设计新用户引导流程", deadline="2026-05-29", priority="medium"),
        ],
        disputes=[
            Dispute(
                topic="前端框架选型",
                positions=["React: 团队熟悉度高", "Vue: 生态更轻量"],
                status="unresolved",
            ),
        ],
    )


class TestMeetingMinutesMarkdown:
    """Markdown output tests."""

    def test_contains_title(self, sample_minutes):
        md = sample_minutes.to_markdown()
        assert "Q2 产品规划会" in md

    def test_contains_participants(self, sample_minutes):
        md = sample_minutes.to_markdown()
        assert "张三" in md
        assert "李四" in md

    def test_contains_decisions(self, sample_minutes):
        md = sample_minutes.to_markdown()
        assert "支付模块重构" in md
        assert "微服务" in md

    def test_contains_action_items(self, sample_minutes):
        md = sample_minutes.to_markdown()
        assert "张三" in md
        assert "技术方案" in md

    def test_contains_disputes(self, sample_minutes):
        md = sample_minutes.to_markdown()
        assert "前端框架" in md
        assert "unresolved" in md


class TestMeetingMinutesJSON:
    """JSON output tests."""

    def test_valid_json(self, sample_minutes):
        result = sample_minutes.to_json()
        data = json.loads(result)
        assert data["title"] == "Q2 产品规划会"
        assert len(data["decisions"]) == 1
        assert len(data["action_items"]) == 2

    def test_json_structure(self, sample_minutes):
        data = json.loads(sample_minutes.to_json())
        assert "summary" in data
        assert "topics" in data
        assert "processing_stats" in data


class TestMeetingMinutesBrief:
    """Brief output tests."""

    def test_brief_format(self, sample_minutes):
        brief = sample_minutes.to_brief()
        assert "Q2 产品规划会" in brief
        assert "决策 1 项" in brief
        assert "行动项 2 条" in brief
