"""MeetingTruth batch audit runner.

Usage:
    python run_audit.py --cases all
    python run_audit.py --cases missing_attendee
    python run_audit.py --cases ambiguous_owner,no_decision
    python run_audit.py --report
    python run_audit.py --generate          # re-generate all 50 test cases
    python run_audit.py --index             # (re-)index ground truth into ChromaDB
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TRANSCRIPTS_DIR = Path("audit_cases/raw_transcripts")
RESULTS_DIR = Path("audit_cases/results")
CSV_PATH = RESULTS_DIR / "audit_results.csv"

_DEFECT_TYPES = [
    "missing_attendee",
    "ambiguous_owner",
    "conflicting_deadline",
    "no_decision",
    "implicit_action",
]

_CSV_COLUMNS = [
    "transcript_id",
    "defect_type",
    "hallucination_score",
    "misattribution_count",
    "missing_items_count",
    "fabrication_count",
    "overall_risk",
]


# ── helpers ────────────────────────────────────────────────────────────────────

def _load_cases(defect_filter: list[str]) -> list[tuple[str, str, str]]:
    """Return (transcript_id, transcript_text, defect_type) tuples."""
    cases: list[tuple[str, str, str]] = []
    for txt_path in sorted(TRANSCRIPTS_DIR.glob("*.txt")):
        tid = txt_path.stem
        # Derive defect type from ID prefix (e.g. "missing-attendee-001" → "missing_attendee")
        prefix = "-".join(tid.split("-")[:-1]).replace("-", "_")
        if defect_filter and prefix not in defect_filter:
            continue
        transcript = txt_path.read_text(encoding="utf-8")
        cases.append((tid, transcript, prefix))
    return cases


def _write_csv(rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in _CSV_COLUMNS})
    print(f"\nResults written to {CSV_PATH}")


def _print_report() -> None:
    from src.mcp.tools.get_audit_summary import get_audit_summary
    summary = get_audit_summary()
    if "error" in summary:
        print(f"[ERROR] {summary['error']}")
        return

    print("\n" + "=" * 60)
    print("  MeetingTruth Audit Summary")
    print("=" * 60)
    print(f"  Total cases audited : {summary['total_cases']}")
    print(f"  Avg hallucination   : {summary['avg_hallucination_score']:.3f}")
    print()
    print("  Risk distribution:")
    for risk, count in summary.get("overall_risk_distribution", {}).items():
        print(f"    {risk:10s}: {count}")
    print()
    print("  Hallucination types:")
    for htype, count in summary.get("hallucination_type_breakdown", {}).items():
        print(f"    {htype:25s}: {count}")
    print()
    print("  By defect type:")
    for defect, stats in summary.get("by_defect_type", {}).items():
        print(
            f"    {defect:28s}: {stats['cases']} cases, "
            f"score={stats['avg_hallucination_score']:.3f}, "
            f"high_risk={stats['high_risk_count']}"
        )
    print("=" * 60)


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="MeetingTruth batch audit runner")
    parser.add_argument(
        "--cases",
        default="",
        help=(
            "Comma-separated defect type(s) to audit, or 'all'. "
            "E.g. --cases all  OR  --cases missing_attendee,no_decision"
        ),
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print aggregated audit summary and exit (no new audits run).",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="(Re-)generate all 50 synthetic test cases and exit.",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="(Re-)index ground-truth files into ChromaDB and exit.",
    )
    args = parser.parse_args()

    # ── generate ──────────────────────────────────────────────────────────────
    if args.generate:
        from src.synthesis.case_generator import CaseGenerator
        gen = CaseGenerator()
        results = gen.generate_all()
        total = sum(len(v) for v in results.values())
        print(f"Generated {total} cases:")
        for dt, ids in results.items():
            print(f"  {dt}: {len(ids)} cases → {ids[0]} … {ids[-1]}")
        return

    # ── index ─────────────────────────────────────────────────────────────────
    if args.index:
        from src.core.config import get_settings
        from src.rag.indexer import GroundTruthIndexer
        settings = get_settings()
        indexer = GroundTruthIndexer(persist_dir=settings.chroma_persist_dir)
        count = indexer.index_all()
        print(f"Indexed {count} ground-truth documents into ChromaDB.")
        return

    # ── report ────────────────────────────────────────────────────────────────
    if args.report:
        _print_report()
        return

    # ── audit run ─────────────────────────────────────────────────────────────
    if not args.cases:
        parser.print_help()
        sys.exit(1)

    defect_filter: list[str] = (
        [] if args.cases.strip().lower() == "all"
        else [d.strip() for d in args.cases.split(",")]
    )

    # Validate requested defect types
    for dt in defect_filter:
        if dt not in _DEFECT_TYPES:
            print(f"[ERROR] Unknown defect type: '{dt}'. Valid: {_DEFECT_TYPES}")
            sys.exit(1)

    cases = _load_cases(defect_filter)
    if not cases:
        print("[ERROR] No transcript files found. Run with --generate first.")
        sys.exit(1)

    print(f"\nAuditing {len(cases)} case(s) …\n")

    from src.agent.audit_agent import AuditAgent
    agent = AuditAgent()
    csv_rows: list[dict] = []
    failed = 0

    for i, (tid, transcript, defect_type) in enumerate(cases, 1):
        prefix = f"[{i:3d}/{len(cases)}] {tid}"
        try:
            print(f"{prefix} … ", end="", flush=True)
            result = agent.audit(tid, transcript, defect_type)
            print(
                f"score={result.hallucination_score:.2f}  "
                f"risk={result.overall_risk}  "
                f"flags={len(result.hallucination_flags)}"
            )
            csv_rows.append({
                "transcript_id": result.transcript_id,
                "defect_type": result.defect_type,
                "hallucination_score": f"{result.hallucination_score:.4f}",
                "misattribution_count": result.misattribution_count,
                "missing_items_count": result.missing_items_count,
                "fabrication_count": result.fabrication_count,
                "overall_risk": result.overall_risk,
            })
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED — {exc}")
            failed += 1

    if csv_rows:
        _write_csv(csv_rows)

    print(f"\nDone. {len(csv_rows)} succeeded, {failed} failed.")
    if csv_rows:
        _print_report()


if __name__ == "__main__":
    main()
