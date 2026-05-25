"""Aggregate all audit results into a summary report."""
import json
from collections import defaultdict
from pathlib import Path

RESULTS_DIR = Path("audit_cases/results")
LOG_FILE = RESULTS_DIR / "audit_log.jsonl"


def get_audit_summary() -> dict:
    """Read audit_log.jsonl and return aggregated statistics."""
    if not LOG_FILE.exists():
        return {"error": "No audit log found. Run audits first with run_audit.py."}

    results: list[dict] = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    if not results:
        return {"total_cases": 0}

    by_defect: dict[str, list] = defaultdict(list)
    by_risk: dict[str, int] = defaultdict(int)
    hallucination_types: dict[str, int] = defaultdict(int)

    for r in results:
        by_defect[r.get("defect_type", "unknown")].append(r)
        by_risk[r.get("overall_risk", "unknown")] += 1
        for flag in r.get("hallucination_flags", []):
            hallucination_types[flag.get("hallucination_type", "unknown")] += 1

    scores = [r.get("hallucination_score", 0.0) for r in results]

    defect_summary = {}
    for defect, items in by_defect.items():
        defect_scores = [i.get("hallucination_score", 0.0) for i in items]
        defect_summary[defect] = {
            "cases": len(items),
            "avg_hallucination_score": round(sum(defect_scores) / len(defect_scores), 3),
            "high_risk_count": sum(1 for i in items if i.get("overall_risk") == "high"),
        }

    return {
        "total_cases": len(results),
        "avg_hallucination_score": round(sum(scores) / len(scores), 3),
        "overall_risk_distribution": dict(by_risk),
        "hallucination_type_breakdown": dict(hallucination_types),
        "by_defect_type": defect_summary,
    }
