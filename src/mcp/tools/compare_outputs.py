"""Field-by-field diff between ground truth and AI-generated meeting output."""
from __future__ import annotations

from typing import Any


def _as_set(val: Any) -> set:
    if isinstance(val, list):
        return {str(v).strip().lower() for v in val}
    return {str(val).strip().lower()} if val else set()


def _action_text(item: Any) -> str:
    if isinstance(item, dict):
        return item.get("action", "")
    return getattr(item, "action", "")


def _action_field(item: Any, field: str) -> str | None:
    if isinstance(item, dict):
        return item.get(field)
    return getattr(item, field, None)


def compare_outputs(ground_truth: dict, ai_output: dict) -> dict:
    """Return a structured diff of discrepancies between ground truth and AI output.

    Both inputs are expected to follow the MeetingSummary schema shape.
    """
    discrepancies: list[dict] = []

    # ── attendees ──────────────────────────────────────────────────────────────
    gt_att = _as_set(ground_truth.get("attendees", []))
    ai_att = _as_set(ai_output.get("attendees", []))
    extra = ai_att - gt_att
    missing = gt_att - ai_att
    if extra:
        discrepancies.append({
            "field": "attendees",
            "type": "extra",
            "ai_value": list(extra),
            "gt_value": list(gt_att),
            "description": f"AI added attendees not in transcript: {extra}",
        })
    if missing:
        discrepancies.append({
            "field": "attendees",
            "type": "missing",
            "ai_value": list(ai_att),
            "gt_value": list(missing),
            "description": f"AI omitted attendees: {missing}",
        })

    # ── decisions ──────────────────────────────────────────────────────────────
    gt_dec = ground_truth.get("decisions", [])
    ai_dec = ai_output.get("decisions", [])
    if len(ai_dec) > len(gt_dec):
        discrepancies.append({
            "field": "decisions",
            "type": "extra",
            "ai_value": ai_dec,
            "gt_value": gt_dec,
            "description": (
                f"AI found {len(ai_dec)} decisions; ground truth has {len(gt_dec)}"
            ),
        })
    elif len(ai_dec) < len(gt_dec):
        discrepancies.append({
            "field": "decisions",
            "type": "missing",
            "ai_value": ai_dec,
            "gt_value": gt_dec,
            "description": (
                f"AI missed {len(gt_dec) - len(ai_dec)} decision(s)"
            ),
        })

    # ── action_items ───────────────────────────────────────────────────────────
    gt_actions = ground_truth.get("action_items", [])
    ai_actions = ai_output.get("action_items", [])

    if len(ai_actions) > len(gt_actions):
        discrepancies.append({
            "field": "action_items",
            "type": "extra",
            "ai_value": len(ai_actions),
            "gt_value": len(gt_actions),
            "description": (
                f"AI generated {len(ai_actions)} action items; "
                f"ground truth has {len(gt_actions)}"
            ),
        })

    for i, ai_action in enumerate(ai_actions):
        ai_text = _action_text(ai_action).lower()
        # find best-matching GT action by text overlap
        matched_gt = None
        for gt_action in gt_actions:
            gt_text = _action_text(gt_action).lower()
            if gt_text[:25] in ai_text or ai_text[:25] in gt_text:
                matched_gt = gt_action
                break

        if matched_gt is None:
            if i < len(gt_actions):
                matched_gt = gt_actions[i]

        if matched_gt is None:
            discrepancies.append({
                "field": f"action_items[{i}]",
                "type": "fabrication",
                "ai_value": _action_text(ai_action),
                "gt_value": "",
                "description": "AI fabricated an action item with no counterpart in ground truth",
            })
            continue

        # owner mismatch
        ai_owner = (_action_field(ai_action, "owner") or "").strip()
        gt_owner = (_action_field(matched_gt, "owner") or "").strip()
        if ai_owner.lower() != gt_owner.lower():
            discrepancies.append({
                "field": f"action_items[{i}].owner",
                "type": "misattribution",
                "ai_value": ai_owner,
                "gt_value": gt_owner,
                "description": f"AI assigned action to '{ai_owner}'; ground truth is '{gt_owner}'",
            })

        # deadline mismatch
        ai_dl = _action_field(ai_action, "deadline")
        gt_dl = _action_field(matched_gt, "deadline")
        if str(ai_dl or "").strip().lower() != str(gt_dl or "").strip().lower():
            discrepancies.append({
                "field": f"action_items[{i}].deadline",
                "type": "wrong_deadline",
                "ai_value": str(ai_dl),
                "gt_value": str(gt_dl),
                "description": f"AI set deadline '{ai_dl}'; ground truth is '{gt_dl}'",
            })

    return {
        "discrepancies": discrepancies,
        "total_discrepancies": len(discrepancies),
        "attendee_discrepancies": sum(1 for d in discrepancies if "attendees" in d["field"]),
        "decision_discrepancies": sum(1 for d in discrepancies if "decisions" in d["field"]),
        "action_item_discrepancies": sum(1 for d in discrepancies if "action_items" in d["field"]),
    }
