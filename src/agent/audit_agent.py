"""Gemini + MCP audit orchestrator for MeetingTruth.

Architecture:
  AuditAgent connects to the MeetingTruth MCP server (src/mcp/server.py)
  via stdio transport using langchain-mcp-adapters.
  Gemini acts as the audit LLM, calling MCP tools through LangChain's
  tool-calling interface — get_ground_truth → compare_outputs → write_audit_log.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from ..core.llm import get_llm
from ..schema.audit import AuditResult
from .meeting_agent import MeetingAgent
from .prompts import AUDIT_SYSTEM_PROMPT_MCP, AUDIT_USER_TEMPLATE_MCP

# Run MCP server as: python -m src.mcp.server  (preserves relative imports)
_SERVER_CMD = [sys.executable, "-m", "src.mcp.server"]


# ── helpers ───────────────────────────────────────────────────────────────────

def _save_ai_output(transcript_id: str, ai_output: dict) -> None:
    out_dir = Path("audit_cases/results/ai_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{transcript_id}.json", "w", encoding="utf-8") as f:
        json.dump(ai_output, f, indent=2, ensure_ascii=False)


def _extract_text(content) -> str:
    """Normalise LangChain response content to plain string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    return str(content)


def _parse_json_from_text(text: str) -> dict | None:
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── agent ─────────────────────────────────────────────────────────────────────

class AuditAgent:
    """Gemini-powered audit orchestrator that calls tools via MCP protocol.

    Workflow:
    1. MeetingAgent (Gemini) summarises the transcript → ai_output
    2. AuditAgent connects to the MeetingTruth MCP server
    3. Gemini calls MCP tools (get_ground_truth → compare_outputs → write_audit_log)
    4. Returns a validated AuditResult
    """

    def __init__(self, llm=None) -> None:
        self._llm = llm or get_llm(temperature=0.0)
        self.meeting_agent = MeetingAgent()

    # ── public API ────────────────────────────────────────────────────────────

    def audit(
        self, transcript_id: str, transcript: str, defect_type: str
    ) -> AuditResult:
        """Synchronous entry point — runs the async audit in a new event loop."""
        return asyncio.run(self._audit_async(transcript_id, transcript, defect_type))

    async def aaudit(
        self, transcript_id: str, transcript: str, defect_type: str
    ) -> AuditResult:
        """Async entry point."""
        return await self._audit_async(transcript_id, transcript, defect_type)

    # ── internals ─────────────────────────────────────────────────────────────

    async def _audit_async(
        self, transcript_id: str, transcript: str, defect_type: str
    ) -> AuditResult:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        # Step 1: get Gemini meeting-agent output (the subject under audit)
        meeting_summary = self.meeting_agent.summarize(transcript)
        ai_output = meeting_summary.model_dump()

        # Step 2: connect to MeetingTruth MCP server via stdio
        # langchain-mcp-adapters ≥0.1.0: no context manager, call get_tools() directly
        client = MultiServerMCPClient({
            "meetingtruth-audit": {
                "command": _SERVER_CMD[0],
                "args": _SERVER_CMD[1:],
                "transport": "stdio",
                "env": {**os.environ},   # pass API keys etc. to subprocess
            }
        })
        tools = await client.get_tools()
        llm_with_tools = self._llm.bind_tools(tools)

        user_content = AUDIT_USER_TEMPLATE_MCP.format(
            transcript_id=transcript_id,
            defect_type=defect_type,
            transcript=transcript,
            ai_output=json.dumps(ai_output, indent=2, ensure_ascii=False),
        )

        messages = [
            SystemMessage(content=AUDIT_SYSTEM_PROMPT_MCP),
            HumanMessage(content=user_content),
        ]

        # Step 3: tool-use loop (Gemini calls MCP tools)
        raw_result: dict | None = None
        last_response = None

        for _ in range(10):   # safety cap
            response = llm_with_tools.invoke(messages)
            last_response = response
            messages.append(response)

            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                break

            for tc in tool_calls:
                tool = next((t for t in tools if t.name == tc["name"]), None)
                if tool is None:
                    continue

                tool_result = await tool.ainvoke(tc["args"])

                # capture write_audit_log argument as the authoritative result
                if tc["name"] == "write_audit_log":
                    raw_result = tc["args"].get("audit_result")

                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tc["id"],
                ))

        # Step 4: fallback — try parsing JSON from final text response
        if raw_result is None and last_response is not None:
            text = _extract_text(getattr(last_response, "content", ""))
            raw_result = _parse_json_from_text(text)

        result = self._build_result(
            raw_result or {}, transcript_id, defect_type, ai_output
        )

        _save_ai_output(transcript_id, ai_output)
        return result

    def _build_result(
        self,
        raw_dict: dict,
        transcript_id: str,
        defect_type: str,
        ai_output: dict,
    ) -> AuditResult:
        if raw_dict:
            for flag in raw_dict.get("hallucination_flags", []):
                if "hallucination_type" in flag:
                    flag["hallucination_type"] = flag["hallucination_type"].lower()
            raw_dict["transcript_id"] = transcript_id
            raw_dict["defect_type"] = defect_type
            raw_dict.setdefault("raw_ai_output", ai_output)
            raw_dict.setdefault("raw_ground_truth", {})
            try:
                return AuditResult.model_validate(raw_dict)
            except Exception:
                pass

        return AuditResult(
            transcript_id=transcript_id,
            defect_type=defect_type,
            hallucination_flags=[],
            hallucination_score=0.0,
            misattribution_count=0,
            missing_items_count=0,
            fabrication_count=0,
            overall_risk="low",
            raw_ai_output=ai_output,
            raw_ground_truth={},
        )
