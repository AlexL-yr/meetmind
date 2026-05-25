"""Pydantic schemas for MeetingTruth audit results."""
from enum import Enum
from typing import List

from pydantic import BaseModel


class HallucinationType(str, Enum):
    FABRICATION = "fabrication"
    OMISSION = "omission"
    MISATTRIBUTION = "misattribution"
    FALSE_DECISION = "false_decision"
    INFERRED_TASK = "inferred_task"


class HallucinationFlag(BaseModel):
    field: str
    hallucination_type: HallucinationType
    ai_output: str
    ground_truth: str
    severity: str       # "high" | "medium" | "low"
    ethical_risk: str   # plain-text ethical implication


class AuditResult(BaseModel):
    transcript_id: str
    defect_type: str
    hallucination_flags: List[HallucinationFlag]
    hallucination_score: float          # 0.0 – 1.0
    misattribution_count: int
    missing_items_count: int
    fabrication_count: int
    overall_risk: str                   # "high" | "medium" | "low"
    raw_ai_output: dict
    raw_ground_truth: dict
