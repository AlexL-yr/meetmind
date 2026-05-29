"""MeetingTruth MCP server — exposes audit tools for Claude Desktop / MCP clients."""
import json

from mcp.server.fastmcp import FastMCP

from .tools.compare_outputs import compare_outputs as _compare_outputs
from .tools.get_audit_summary import get_audit_summary as _get_audit_summary
from .tools.get_ground_truth import get_ground_truth as _get_ground_truth
from .tools.search_ground_truth import search_ground_truth as _search_ground_truth
from .tools.write_audit_log import write_audit_log as _write_audit_log

mcp = FastMCP("meetingtruth-audit")


@mcp.tool()
def get_ground_truth(transcript_id: str) -> str:
    """Retrieve the correct expected output for a transcript from the ground-truth store.

    Args:
        transcript_id: Identifier matching a file in audit_cases/ground_truth/

    Returns:
        JSON string of the ground-truth dict, or an error message.
    """
    result = _get_ground_truth(transcript_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def write_audit_log(audit_result: dict) -> str:
    """Persist a completed AuditResult to the append-only audit log.

    Args:
        audit_result: AuditResult dict matching the MeetingTruth schema.

    Returns:
        Confirmation string.
    """
    return _write_audit_log(audit_result)


@mcp.tool()
def compare_outputs(ground_truth: dict, ai_output: dict) -> str:
    """Field-by-field diff between ground truth and AI-generated meeting output.

    Args:
        ground_truth: Expected correct MeetingSummary dict.
        ai_output: AI-generated MeetingSummary dict to evaluate.

    Returns:
        JSON string with discrepancies list and counts by category.
    """
    result = _compare_outputs(ground_truth, ai_output)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def search_ground_truth(query: str, n_results: int = 3) -> str:
    """Find the most semantically similar ground-truth cases for a free-text query.

    Args:
        query: Transcript excerpt or keyword description to search for.
        n_results: Number of results to return (default 3).

    Returns:
        JSON string with list of similar ground-truth dicts ordered by cosine similarity.
    """
    result = _search_ground_truth(query, n_results=n_results)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_audit_summary() -> str:
    """Aggregate all audit results: hallucination rate, breakdown by defect type.

    Returns:
        JSON string with summary statistics.
    """
    result = _get_audit_summary()
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
