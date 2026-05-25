"""Claude-powered audit orchestrator for MeetingTruth."""
from __future__ import annotations

import json
import re
from typing import Any

from ..core.llm import get_claude_client, get_claude_model_name
from ..mcp.tools.compare_outputs import compare_outputs
from ..mcp.tools.get_ground_truth import get_ground_truth
from ..mcp.tools.write_audit_log import write_audit_log
from ..schema.audit import AuditResult, HallucinationFlag, HallucinationType
from .meeting_agent import MeetingAgent
from .prompts import AUDIT_SYSTEM_PROMPT, AUDIT_USER_TEMPLATE

# ── Anthropic tool schemas (mirror the MCP server tools) ─────────────────────

_AUDIT_TOOLS: list[dict] = [
    {
        "name": "get_ground_truth",
        "description": "Retrieve the correct expected output for a transcript from the ground-truth store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transcript_id": {"type": "string", "description": "Transcript identifier"},
            },
            "required": ["transcript_id"],
        },
    },
    {
        "name": "compare_outputs",
        "description": "Field-by-field diff between ground truth and AI output. Returns discrepancies list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ground_truth": {"type": "object", "description": "Expected correct MeetingSummary dict"},
                "ai_output": {"type": "object", "description": "AI-generated MeetingSummary dict"},
            },
            "required": ["ground_truth", "ai_output"],
        },
    },
    {
        "name": "write_audit_log",
        "description": "Persist the final AuditResult to the audit log. Call this last.",
        "input_schema": {
            "type": "object",
            "properties": {
                "audit_result": {
                    "type": "object",
                    "description": "Complete AuditResult JSON matching the MeetingTruth schema",
                },
            },
            "required": ["audit_result"],
        },
    },
]


def _execute_tool(name: str, inputs: dict) -> Any:
    """Dispatch a tool call to its Python implementation."""
    if name == "get_ground_truth":
        return get_ground_truth(**inputs)
    if name == "compare_outputs":
        return compare_outputs(**inputs)
    if name == "write_audit_log":
        return write_audit_log(**inputs)
    return {"error": f"Unknown tool: {name}"}


def _extract_audit_result_from_tool_call(messages: list[dict]) -> dict | None:
    """Find the write_audit_log tool call and return its audit_result argument."""
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        if block.get("name") == "write_audit_log":
                            return block.get("input", {}).get("audit_result")
    return None


def _parse_json_from_text(text: str) -> dict | None:
    """Extract the first JSON object from a text block (fallback parser)."""
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


class AuditAgent:
    """Claude-powered audit orchestrator.

    Workflow:
    1. Get Gemini's MeetingSummary for the transcript.
    2. Run a tool-use loop with Claude to:
       a. Retrieve ground truth via get_ground_truth
       b. Compare outputs via compare_outputs
       c. Classify each discrepancy as a HallucinationType
       d. Write the final AuditResult via write_audit_log
    3. Parse and return the AuditResult.
    """

    def __init__(self) -> None:
        self.client = get_claude_client()
        self.model = get_claude_model_name()
        self.meeting_agent = MeetingAgent()

    def audit(
        self, transcript_id: str, transcript: str, defect_type: str
    ) -> AuditResult:
        """Run a full audit pass and return a validated AuditResult."""
        # Step 1: get Gemini's output (the subject under audit)
        meeting_summary = self.meeting_agent.summarize(transcript)
        ai_output = meeting_summary.model_dump()

        # Step 2: build initial user message
        user_content = AUDIT_USER_TEMPLATE.format(
            transcript_id=transcript_id,
            defect_type=defect_type,
            transcript=transcript,
            ai_output=json.dumps(ai_output, indent=2, ensure_ascii=False),
        )

        messages: list[dict] = [{"role": "user", "content": user_content}]

        # Step 3: agentic tool-use loop
        raw_result: dict | None = None
        for _ in range(8):  # guard against infinite loops
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=AUDIT_SYSTEM_PROMPT,
                tools=_AUDIT_TOOLS,
                messages=messages,
            )

            # Collect assistant turn
            assistant_content = [b.model_dump() for b in response.content]
            messages.append({"role": "assistant", "content": assistant_content})

            if response.stop_reason == "end_turn":
                # Try to extract result from write_audit_log call made earlier
                raw_result = _extract_audit_result_from_tool_call(messages)
                break

            if response.stop_reason != "tool_use":
                break

            # Execute every tool call in this turn
            tool_results: list[dict] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_output = _execute_tool(block.name, block.input)
                # Capture write_audit_log argument as the authoritative result
                if block.name == "write_audit_log":
                    raw_result = block.input.get("audit_result")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(tool_output, ensure_ascii=False, default=str),
                })

            messages.append({"role": "user", "content": tool_results})

        # Step 4: build AuditResult, with fallback text parse if needed
        if raw_result is None:
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    for block in (msg.get("content") or []):
                        if isinstance(block, dict) and block.get("type") == "text":
                            raw_result = _parse_json_from_text(block.get("text", ""))
                            if raw_result:
                                break
                if raw_result:
                    break

        if raw_result is None:
            # Minimal fallback so the caller always gets a typed object
            raw_result = {
                "transcript_id": transcript_id,
                "defect_type": defect_type,
                "hallucination_flags": [],
                "hallucination_score": 0.0,
                "misattribution_count": 0,
                "missing_items_count": 0,
                "fabrication_count": 0,
                "overall_risk": "low",
                "raw_ai_output": ai_output,
                "raw_ground_truth": {},
            }

        # Normalise hallucination_type strings to enum values
        for flag in raw_result.get("hallucination_flags", []):
            if "hallucination_type" in flag:
                flag["hallucination_type"] = flag["hallucination_type"].lower()

        return AuditResult.model_validate(raw_result)

    async def aaudit(
        self, transcript_id: str, transcript: str, defect_type: str
    ) -> AuditResult:
        """Async wrapper — delegates to sync audit() for now."""
        return self.audit(transcript_id, transcript, defect_type)
