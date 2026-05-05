"""Output formatting for meeting minutes and summaries."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class ActionItem:
    """An action item extracted from the meeting."""

    owner: str
    task: str
    deadline: str = ""
    priority: str = "medium"


@dataclass
class Decision:
    """A decision made during the meeting."""

    topic: str
    decision: str
    rationale: str = ""


@dataclass
class Dispute:
    """A dispute or unresolved discussion point."""

    topic: str
    positions: list[str] = field(default_factory=list)
    status: str = "unresolved"


@dataclass
class MeetingMinutes:
    """Structured meeting minutes."""

    title: str = ""
    date: str = ""
    duration_estimate: str = ""
    participants: list[str] = field(default_factory=list)
    summary: str = ""
    topics: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    disputes: list[Dispute] = field(default_factory=list)
    raw_text: str = ""
    processing_stats: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Format as Markdown."""
        lines = []
        lines.append(f"# {self.title or '会议纪要'}")
        lines.append("")

        if self.date:
            lines.append(f"**日期**: {self.date}")
        if self.duration_estimate:
            lines.append(f"**时长**: {self.duration_estimate}")
        if self.participants:
            lines.append(f"**参会人**: {', '.join(self.participants)}")
        lines.append("")

        if self.summary:
            lines.append("## 📋 摘要")
            lines.append(self.summary)
            lines.append("")

        if self.topics:
            lines.append("## 📝 议题")
            for t in self.topics:
                lines.append(f"### {t.get('title', '议题')}")
                lines.append(t.get("content", ""))
                lines.append("")

        if self.decisions:
            lines.append("## ✅ 决策")
            for d in self.decisions:
                lines.append(f"- **{d.topic}**: {d.decision}")
                if d.rationale:
                    lines.append(f"  - 理由: {d.rationale}")
            lines.append("")

        if self.action_items:
            lines.append("## 🎯 行动项")
            for a in self.action_items:
                deadline = f" (截止: {a.deadline})" if a.deadline else ""
                lines.append(f"- [{a.priority}] **{a.owner}**: {a.task}{deadline}")
            lines.append("")

        if self.disputes:
            lines.append("## ⚠️ 待解决争议")
            for disp in self.disputes:
                lines.append(f"- **{disp.topic}** [{disp.status}]")
                for pos in disp.positions:
                    lines.append(f"  - {pos}")
            lines.append("")

        if self.processing_stats:
            lines.append("---")
            lines.append(f"*处理统计: {json.dumps(self.processing_stats, ensure_ascii=False)}*")

        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        """Format as JSON."""
        data = asdict(self)
        return json.dumps(data, ensure_ascii=False, indent=indent)

    def to_brief(self) -> str:
        """One-paragraph brief summary."""
        parts = []
        if self.title:
            parts.append(self.title)
        if self.summary:
            parts.append(self.summary[:200])
        if self.decisions:
            parts.append(f"决策 {len(self.decisions)} 项")
        if self.action_items:
            parts.append(f"行动项 {len(self.action_items)} 条")
        return " | ".join(parts)
