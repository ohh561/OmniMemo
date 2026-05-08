"""Agent dispatcher — routes meetings to appropriate analysis templates."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from omni_memo.config import MiMoConfig

logger = logging.getLogger(__name__)

MEETING_TYPES = {
    "standup": {
        "name_zh": "站会/日报",
        "name_en": "Standup/Daily",
        "template": "focus on blockers, yesterday/today tasks, brief format",
    },
    "weekly": {
        "name_zh": "周会",
        "name_en": "Weekly Review",
        "template": "metrics review, project status, risk flags",
    },
    "tech_review": {
        "name_zh": "技术评审",
        "name_en": "Technical Review",
        "template": "architecture decisions, trade-offs, action items with owners",
    },
    "client": {
        "name_zh": "客户沟通",
        "name_en": "Client Meeting",
        "template": "requirements, commitments, follow-ups, relationship notes",
    },
    "brainstorm": {
        "name_zh": "头脑风暴",
        "name_en": "Brainstorm",
        "template": "idea clustering, feasibility tags, priority votes",
    },
    "general": {
        "name_zh": "通用会议",
        "name_en": "General Meeting",
        "template": "standard minutes with decisions and action items",
    },
}

CLASSIFY_PROMPT_ZH = """根据以下会议内容片段，判断会议类型。

可选类型：standup（站会）、weekly（周会）、tech_review（技术评审）、client（客户沟通）、brainstorm（头脑风暴）、general（通用）

输出 JSON：{"type": "类型英文名", "confidence": 0.0-1.0, "reason": "判断理由"}"""

CLASSIFY_PROMPT_EN = """Classify the meeting type from the following excerpt.
Types: standup, weekly, tech_review, client, brainstorm, general
Output JSON: {"type": "...", "confidence": 0.0-1.0, "reason": "..."}"""


class AgentDispatcher:
    """Classify meeting type and select appropriate analysis template."""

    def __init__(self, config: MiMoConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def classify(self, excerpt: str, language: str = "zh") -> dict:
        """Classify meeting type from a text excerpt.

        Args:
            excerpt: First ~2000 chars of meeting transcript.
            language: zh or en.

        Returns:
            Dict with type, confidence, reason.
        """
        prompt = CLASSIFY_PROMPT_ZH if language == "zh" else CLASSIFY_PROMPT_EN

        response = self.client.chat.completions.create(
            model=self.config.model_pro,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": excerpt[:2000]},
            ],
            max_tokens=256,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {"type": "general", "confidence": 0.5, "reason": "fallback"}

        return result

    def get_template(self, meeting_type: str, language: str = "zh") -> str:
        """Get the analysis template instructions for a meeting type."""
        info = MEETING_TYPES.get(meeting_type, MEETING_TYPES["general"])
        if language == "zh":
            return f"会议类型：{info['name_zh']}\n分析模板：{info['template']}"
        return f"Meeting type: {info['name_en']}\nTemplate: {info['template']}"
