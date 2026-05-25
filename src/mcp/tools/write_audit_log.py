"""Persist an AuditResult dict to the JSONL audit log."""
import json
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path("audit_cases/results")
LOG_FILE = RESULTS_DIR / "audit_log.jsonl"


def write_audit_log(audit_result: dict) -> str:
    """Append *audit_result* to audit_log.jsonl. Returns a confirmation string."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {**audit_result, "logged_at": datetime.now(timezone.utc).isoformat()}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return f"Logged audit result for transcript_id='{audit_result.get('transcript_id', 'unknown')}'"
