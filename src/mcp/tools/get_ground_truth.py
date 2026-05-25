"""Retrieve the correct expected output for a transcript from the ground-truth store."""
import json
from pathlib import Path

GROUND_TRUTH_DIR = Path("audit_cases/ground_truth")


def get_ground_truth(transcript_id: str) -> dict:
    """Return the ground-truth dict for *transcript_id*, or an error dict."""
    filepath = GROUND_TRUTH_DIR / f"{transcript_id}.json"
    if not filepath.exists():
        return {"error": f"No ground truth found for transcript_id='{transcript_id}'"}
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)
