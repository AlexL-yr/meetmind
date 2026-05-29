"""Meeting summarization agent — uses local Ollama LLM (subject under audit).

The Ollama model simulates a commercial meeting summarization system.
It is the *target* of the MeetingTruth audit, not the auditor.
"""
from __future__ import annotations

import json
import re

from ..core.llm import get_ollama_llm
from ..schema.meeting import MeetingSummary
from .prompts import MEETING_SYSTEM_PROMPT, MEETING_USER_TEMPLATE


def _parse_meeting_summary(text: str) -> MeetingSummary:
    """Extract JSON from raw LLM text and validate against MeetingSummary."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    match = re.search(r"\{[\s\S]+\}", text)
    if not match:
        raise ValueError("No JSON object found in model response")
    return MeetingSummary.model_validate(json.loads(match.group()))


class MeetingAgent:
    """Local-LLM meeting summarizer (Ollama llama3.1:8b).

    Produces structured MeetingSummary output that the AuditAgent then audits.
    Uses with_structured_output when available; falls back to JSON-prompt + parse
    if the local model returns raw text.
    """

    def __init__(self, llm=None) -> None:
        self._llm = llm or get_ollama_llm(temperature=0.1)
        self._structured = self._llm.with_structured_output(MeetingSummary)

    def summarize(self, meeting_content: str) -> MeetingSummary:
        messages = [
            {"role": "system", "content": MEETING_SYSTEM_PROMPT},
            {"role": "user", "content": MEETING_USER_TEMPLATE.format(
                meeting_content=meeting_content
            )},
        ]
        try:
            result = self._structured.invoke(messages)
            if isinstance(result, MeetingSummary):
                return result
        except Exception:
            pass

        # Fallback: raw invoke + JSON parse
        raw = self._llm.invoke(messages)
        content = raw.content if hasattr(raw, "content") else str(raw)
        if isinstance(content, list):
            content = "\n".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )
        return _parse_meeting_summary(content)

    async def asummarize(self, meeting_content: str) -> MeetingSummary:
        messages = [
            {"role": "system", "content": MEETING_SYSTEM_PROMPT},
            {"role": "user", "content": MEETING_USER_TEMPLATE.format(
                meeting_content=meeting_content
            )},
        ]
        try:
            result = await self._structured.ainvoke(messages)
            if isinstance(result, MeetingSummary):
                return result
        except Exception:
            pass

        raw = await self._llm.ainvoke(messages)
        content = raw.content if hasattr(raw, "content") else str(raw)
        if isinstance(content, list):
            content = "\n".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )
        return _parse_meeting_summary(content)


def create_meeting_agent(**kwargs) -> MeetingAgent:
    return MeetingAgent(**kwargs)
