from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


load_dotenv()


class ContentStrategistAgent:
    """LangChain-powered layer for strategy synthesis and chat."""

    def __init__(self) -> None:
        self.model = os.getenv("LLM_MODEL", "").strip()
        self.base_url = os.getenv("LLM_BASE_URL", "").strip()
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self._llm = self._build_llm()

    @property
    def ready(self) -> bool:
        return self._llm is not None

    def create_executive_summary(self, analysis: dict[str, Any]) -> str:
        context = _compact_context(analysis)
        if not self._llm:
            return fallback_executive_summary(analysis)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Bạn là AI Content Strategist cho creator, KOL và doanh nghiệp. "
                    "Luôn trả lời bằng tiếng Việt, súc tích, có số liệu cụ thể, không bịa dữ liệu ngoài context.",
                ),
                (
                    "human",
                    "Hãy viết executive summary cho báo cáo hiệu suất kênh dựa trên JSON sau.\n"
                    "Yêu cầu format Markdown gồm: Tình hình hiện tại, Điểm thắng, Rủi ro, Ưu tiên tháng tới.\n\n"
                    "{context}",
                ),
            ]
        )
        chain = prompt | self._llm | StrOutputParser()
        return chain.invoke({"context": json.dumps(context, ensure_ascii=False, indent=2)})

    def answer(self, message: str, analysis: dict[str, Any] | None = None) -> str:
        if not analysis:
            return "Bạn hãy upload file CSV/Excel trước, rồi mình sẽ phân tích hiệu suất và trả lời theo dữ liệu của kênh."

        context = _compact_context(analysis)
        if not self._llm:
            return (
                fallback_executive_summary(analysis)
                + "\n\nLLM chưa được cấu hình. Set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` trong `.env` để bật chat chiến lược đầy đủ."
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Bạn là AI Content Strategist Agent. Trả lời bằng tiếng Việt, dùng số liệu từ context, "
                    "ưu tiên insight có thể hành động cho TikTok, YouTube hoặc Facebook. Nếu dữ liệu thiếu, nói rõ hạn chế.",
                ),
                (
                    "human",
                    "Context phân tích:\n{context}\n\nCâu hỏi của người dùng: {message}\n\n"
                    "Trả lời như một strategist thực chiến, không dài dòng.",
                ),
            ]
        )
        chain = prompt | self._llm | StrOutputParser()
        return chain.invoke(
            {
                "context": json.dumps(context, ensure_ascii=False, indent=2),
                "message": message,
            }
        )

    def _build_llm(self) -> ChatOpenAI | None:
        if not self.model or not self.base_url:
            return None

        api_key = self.api_key or "not-needed"
        try:
            return ChatOpenAI(
                model=self.model,
                api_key=api_key,
                base_url=self.base_url,
                temperature=self.temperature,
                timeout=float(os.getenv("LLM_TIMEOUT", "60")),
            )
        except TypeError:
            return ChatOpenAI(
                model=self.model,
                openai_api_key=api_key,
                openai_api_base=self.base_url,
                temperature=self.temperature,
            )


def fallback_executive_summary(analysis: dict[str, Any]) -> str:
    summary = analysis.get("summary", {})
    patterns = analysis.get("patterns", {})
    best_video = summary.get("best_video", {})
    best_pillar = summary.get("best_pillar") or {}
    best_slot = summary.get("best_slot") or {}
    calendar = analysis.get("content_calendar", {})

    lines = [
        "## Executive Summary",
        f"- Tổng quan: phân tích {summary.get('total_videos', 0)} video, tổng {summary.get('total_views', 0):,.0f} views và engagement rate trung bình {summary.get('avg_engagement_rate', 0):.2f}%.",
        f"- Video mạnh nhất: {best_video.get('title', 'N/A')} với score {best_video.get('score', 0):.1f}.",
        f"- Pillar hiệu quả nhất: {best_pillar.get('content_pillar', 'N/A')} với score trung bình {best_pillar.get('avg_score', 0):.1f}.",
        f"- Khung giờ ưu tiên: {best_slot.get('slot', 'Chưa đủ dữ liệu')}.",
        f"- Tăng trưởng: {summary.get('growth_outlook', 'Chưa đủ dữ liệu dự báo')}",
        f"- Tháng tới: đề xuất {calendar.get('recommended_posts', summary.get('recommended_posts', 0))} bài cho {calendar.get('month', summary.get('next_calendar_month', 'tháng tiếp theo'))}.",
    ]

    success = patterns.get("success_patterns") or []
    failure = patterns.get("failure_patterns") or []
    if success:
        lines.append("\n### Pattern thắng")
        lines.extend(f"- {item}" for item in success[:4])
    if failure:
        lines.append("\n### Pattern cần xử lý")
        lines.extend(f"- {item}" for item in failure[:3])

    return "\n".join(lines)


def _compact_context(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": analysis.get("summary"),
        "top_videos": (analysis.get("per_video") or [])[:10],
        "pillar_performance": analysis.get("pillar_performance"),
        "optimal_time": analysis.get("optimal_time"),
        "patterns": analysis.get("patterns"),
        "growth_forecast": {
            key: value
            for key, value in (analysis.get("growth_forecast") or {}).items()
            if key not in {"actual", "forecast"}
        },
        "content_calendar": {
            "month": (analysis.get("content_calendar") or {}).get("month"),
            "recommended_posts": (analysis.get("content_calendar") or {}).get("recommended_posts"),
            "strategy": (analysis.get("content_calendar") or {}).get("strategy"),
            "items_preview": ((analysis.get("content_calendar") or {}).get("items") or [])[:8],
        },
    }

