"""MiMo-Pro deep reasoning analyzer — extract decisions, action items, disputes."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from omni_memo.config import MiMoConfig
from omni_memo.utils.formatter import (
    MeetingMinutes, Decision, ActionItem, Dispute,
)

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT_ZH = """你是 OmniMemo 的深度推理引擎。基于以下结构化的会议片段，生成完整的会议纪要。

输入是会议各段落的结构化理解结果（发言人、内容、标签、引用）。

请输出 JSON：
{
  "title": "会议标题（从内容推断）",
  "summary": "200字以内的会议摘要",
  "participants": ["发言人列表"],
  "topics": [
    {
      "title": "议题名称",
      "content": "议题详细内容",
      "sub_topics": ["子议题"]
    }
  ],
  "decisions": [
    {
      "topic": "决策主题",
      "decision": "具体决策",
      "rationale": "决策理由"
    }
  ],
  "action_items": [
    {
      "owner": "负责人",
      "task": "具体任务",
      "deadline": "截止时间（如有）",
      "priority": "high/medium/low"
    }
  ],
  "disputes": [
    {
      "topic": "争议主题",
      "positions": ["各方立场"],
      "status": "unresolved/deferred/resolved"
    }
  ]
}

要求：
1. 发言人识别要准确，合并同一人的不同称呼
2. 决策必须是明确达成共识的内容，不能是建议
3. 行动项必须有明确的负责人
4. 争议标注未达成共识的讨论点"""

ANALYSIS_PROMPT_EN = """You are OmniMemo's deep reasoning engine. Generate structured meeting minutes from the following segments.

Output JSON with: title, summary, participants, topics, decisions, action_items, disputes."""


class ProAnalyzer:
    """Analyze meeting segments via MiMo-Pro deep reasoning."""

    def __init__(self, config: MiMoConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
        )

    def analyze(self, segments: list[dict], language: str = "zh") -> MeetingMinutes:
        """Generate structured meeting minutes from processed segments."""
        prompt = ANALYSIS_PROMPT_ZH if language == "zh" else ANALYSIS_PROMPT_EN

        # Prepare segments as context
        segments_text = json.dumps(segments, ensure_ascii=False, indent=2)

        logger.info("Analyzing %d segments with MiMo-Pro", len(segments))

        response = self.client.chat.completions.create(
            model=self.config.model_pro,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"会议片段数据：\n{segments_text}"},
            ],
            max_tokens=self.config.max_output_tokens,
            temperature=self.config.temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        token_usage = response.usage.total_tokens if response.usage else 0

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse Pro response")
            data = {}

        return self._build_minutes(data, token_usage)

    def analyze_with_context(
        self,
        segments: list[dict],
        context: str,
        language: str = "zh",
    ) -> MeetingMinutes:
        """Analyze with additional context (e.g., previous meeting summary)."""
        prompt = ANALYSIS_PROMPT_ZH if language == "zh" else ANALYSIS_PROMPT_EN

        segments_text = json.dumps(segments, ensure_ascii=False, indent=2)

        response = self.client.chat.completions.create(
            model=self.config.model_pro,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"背景信息：\n{context}\n\n会议片段：\n{segments_text}"},
            ],
            max_tokens=self.config.max_output_tokens,
            temperature=self.config.temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        token_usage = response.usage.total_tokens if response.usage else 0

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {}

        return self._build_minutes(data, token_usage)

    def _build_minutes(self, data: dict, token_usage: int) -> MeetingMinutes:
        """Convert parsed JSON to MeetingMinutes object."""
        decisions = [
            Decision(**d) for d in data.get("decisions", [])
        ]
        action_items = [
            ActionItem(**a) for a in data.get("action_items", [])
        ]
        disputes = [
            Dispute(**d) for d in data.get("disputes", [])
        ]

        return MeetingMinutes(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            participants=data.get("participants", []),
            topics=data.get("topics", []),
            decisions=decisions,
            action_items=action_items,
            disputes=disputes,
            processing_stats={"pro_token_usage": token_usage},
        )
