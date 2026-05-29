"""Generate 50 synthetic audit test cases (10 per defect type).

Each case produces:
- audit_cases/raw_transcripts/{id}.txt   — the meeting transcript (defective input)
- audit_cases/ground_truth/{id}.json     — what a careful human would extract

Defect types:
  MISSING_ATTENDEE    — transcript never mentions a person; AI may hallucinate one
  AMBIGUOUS_OWNER     — "someone will handle it"; AI assigns to a specific person
  CONFLICTING_DEADLINE — same task mentioned with two different deadlines
  NO_DECISION         — team explicitly defers; AI marks as decided
  IMPLICIT_ACTION     — vague statement ("we should look into…"); AI makes formal action
"""
from __future__ import annotations

import json
from pathlib import Path

TRANSCRIPTS_DIR = Path("audit_cases/raw_transcripts")
GROUND_TRUTH_DIR = Path("audit_cases/ground_truth")

# ── People pools (name, title) ────────────────────────────────────────────────
_POOLS: list[list[tuple[str, str]]] = [
    [("Alice Chen", "Product Manager"), ("Bob Martinez", "Engineering Lead")],
    [("David Kim", "CTO"), ("Emma Wilson", "Design Lead")],
    [("Frank Thompson", "VP Sales"), ("Grace Liu", "Marketing Director")],
    [("Henry Park", "Backend Developer"), ("Irene Santos", "Frontend Developer")],
    [("James Cooper", "QA Lead"), ("Karen White", "Scrum Master")],
    [("Liam Brown", "Data Scientist"), ("Maria Garcia", "ML Engineer")],
    [("Noah Davis", "DevOps Engineer"), ("Olivia Johnson", "Cloud Architect")],
    [("Peter Chen", "CEO"), ("Quinn Taylor", "COO")],
    [("Ryan Anderson", "Product Lead"), ("Sofia Martinez", "UX Lead")],
    [("Thomas Wilson", "Backend Engineer"), ("Uma Patel", "Frontend Engineer")],
]

_DATES = [
    "January 8, 2025", "February 12, 2025", "March 5, 2025",
    "April 17, 2025", "May 22, 2025", "June 3, 2025",
    "July 14, 2025", "August 26, 2025", "September 9, 2025",
    "October 30, 2025",
]

_TOPICS = [
    "Q2 Product Planning", "Sprint 15 Retrospective", "Infrastructure Migration Review",
    "Customer Feedback Analysis", "API Design Session", "Budget Allocation Meeting",
    "Performance Review Prep", "New Feature Kickoff", "Security Audit Review",
    "Team Hiring Discussion",
]

# ── helpers ───────────────────────────────────────────────────────────────────

def _p(idx: int) -> list[tuple[str, str]]:
    return _POOLS[idx % len(_POOLS)]


def _name(idx: int, person: int = 0) -> str:
    return _p(idx)[person][0]


def _title(idx: int, person: int = 0) -> str:
    return _p(idx)[person][1]


def _date(idx: int) -> str:
    return _DATES[idx % len(_DATES)]


def _topic(idx: int) -> str:
    return _TOPICS[idx % len(_TOPICS)]


# ═══════════════════════════════════════════════════════════════════════════════
# DEFECT 1 — MISSING_ATTENDEE
# Only two people appear in the transcript; AI should not hallucinate a third.
# ═══════════════════════════════════════════════════════════════════════════════

def _missing_attendee(idx: int) -> tuple[str, dict]:
    a, b = _name(idx, 0), _name(idx, 1)
    at, bt = _title(idx, 0), _title(idx, 1)
    date = _date(idx)
    topic = _topic(idx)

    actions = [
        (f"Prepare revised roadmap document", a, "next Friday"),
        (f"Provide technical feasibility assessment", b, "end of week"),
    ]

    transcript = f"""Meeting: {topic}
Date: {date}

{a} ({at}) opened the meeting by reviewing the agenda. She highlighted the key deliverables for the coming sprint and noted that two items from last week remained unresolved.

{b} ({bt}) presented a status update on the current backlog. He flagged a dependency on an external API that was blocking progress on two user stories. He estimated the dependency would be resolved within three business days.

{a} and {b} agreed on next steps. {a} would prepare a revised roadmap document capturing the updated scope, due by next Friday. {b} committed to providing a technical feasibility assessment by end of week.

No other attendees were present. The meeting was adjourned at 3:10 PM."""

    ground_truth = {
        "title": topic,
        "date": date,
        "attendees": [a, b],
        "summary": (
            f"{a} and {b} reviewed the sprint backlog and an external API dependency. "
            f"Next steps were agreed and ownership assigned to each attendee."
        ),
        "decisions": ["Proceed with current sprint scope pending API resolution"],
        "action_items": [
            {"action": actions[0][0], "owner": actions[0][1], "deadline": actions[0][2]},
            {"action": actions[1][0], "owner": actions[1][1], "deadline": actions[1][2]},
        ],
        "notes": None,
        "defect_type": "MISSING_ATTENDEE",
        "defect_description": (
            f"Only {a} and {b} are mentioned. "
            "The AI should not hallucinate additional attendees."
        ),
    }
    return transcript, ground_truth


# ═══════════════════════════════════════════════════════════════════════════════
# DEFECT 2 — AMBIGUOUS_OWNER
# Owner is explicitly unresolved; AI should not assign a specific person.
# ═══════════════════════════════════════════════════════════════════════════════

_AMBIGUOUS_PHRASES = [
    "Someone from the team will need to own this",
    "The team will sort out who handles it in the next planning session",
    "We haven't decided who yet — whoever has bandwidth",
    "Anyone available should pick this up",
    "This needs an owner but we'll figure that out offline",
    "The team collectively agreed to tackle this but no individual was named",
    "We'll assign it in tomorrow's standup",
    "Ownership is TBD pending the hiring decision",
    "Someone will step up — let's not block on this",
    "The responsible party will be confirmed by end of week",
]

def _ambiguous_owner(idx: int) -> tuple[str, dict]:
    a, b = _name(idx, 0), _name(idx, 1)
    at, bt = _title(idx, 0), _title(idx, 1)
    date = _date(idx)
    topic = _topic(idx)
    phrase = _AMBIGUOUS_PHRASES[idx % len(_AMBIGUOUS_PHRASES)]

    transcript = f"""Meeting: {topic}
Date: {date}

{a} ({at}) opened the meeting by presenting three agenda items requiring follow-up action from the previous sprint.

{b} ({bt}) raised a concern about the deployment pipeline, which caused a 90-minute service disruption. Both agreed a post-mortem document was necessary before the next release.

When asked who would own the post-mortem, {a} said: "{phrase}."

{b} also noted the team's onboarding documentation was out of date. They agreed it needed updating before the next new hire starts, but again the discussion of ownership was explicitly tabled: "We'll figure out who does it — we're already over capacity this sprint."

The meeting concluded with no owners formally assigned to either task."""

    ground_truth = {
        "title": topic,
        "date": date,
        "attendees": [a, b],
        "summary": (
            f"{a} and {b} discussed a deployment pipeline outage and outdated onboarding docs. "
            "Both action items require owners, but ownership was explicitly left unresolved."
        ),
        "decisions": [],
        "action_items": [
            {
                "action": "Write post-mortem document for deployment pipeline outage",
                "owner": "TBD",
                "deadline": None,
            },
            {
                "action": "Update onboarding documentation before next new hire",
                "owner": "TBD",
                "deadline": None,
            },
        ],
        "notes": "Ownership for both action items explicitly deferred. To be resolved in next planning session.",
        "defect_type": "AMBIGUOUS_OWNER",
        "defect_description": (
            "Action item owners are explicitly unresolved in the transcript. "
            "The AI should not assign specific names as owners."
        ),
    }
    return transcript, ground_truth


# ═══════════════════════════════════════════════════════════════════════════════
# DEFECT 3 — CONFLICTING_DEADLINE
# Same task mentioned with two different deadlines; AI should flag the conflict.
# ═══════════════════════════════════════════════════════════════════════════════

_DEADLINE_PAIRS = [
    ("end of Q1", "mid-May"),
    ("by March 31st", "before the summer break"),
    ("next Friday", "end of the month"),
    ("before the product launch in April", "by end of June at the latest"),
    ("two weeks from now", "by the end of the quarter"),
    ("before the board meeting on Thursday", "sometime in Q3"),
    ("by February 1st", "before Easter"),
    ("this sprint", "next quarter"),
    ("within 10 business days", "by year-end"),
    ("before the code freeze", "after the beta release"),
]

def _conflicting_deadline(idx: int) -> tuple[str, dict]:
    a, b = _name(idx, 0), _name(idx, 1)
    at, bt = _title(idx, 0), _title(idx, 1)
    date = _date(idx)
    topic = _topic(idx)
    dl1, dl2 = _DEADLINE_PAIRS[idx % len(_DEADLINE_PAIRS)]

    transcript = f"""Meeting: {topic}
Date: {date}

{a} ({at}) opened by reviewing the timeline for the database migration project, which is critical for the upcoming platform upgrade.

{b} ({bt}) confirmed the migration had been scoped and the initial estimate was {dl1}. This was recorded in the project plan at the start of the quarter.

Later in the meeting, while discussing resource constraints, {a} said: "Given the team's current capacity and the two vacancies we're trying to fill, I think realistically we're looking at {dl2} for the full migration to be complete."

{b} acknowledged the revised estimate but expressed concern about downstream dependencies. No resolution was reached and the conflicting timelines were not reconciled before the meeting ended.

The meeting closed without a confirmed deadline for the database migration."""

    ground_truth = {
        "title": topic,
        "date": date,
        "attendees": [a, b],
        "summary": (
            f"{a} and {b} discussed the database migration timeline. "
            f"A deadline conflict was identified: the project was originally scoped for {dl1}, "
            f"but {a}'s revised estimate is {dl2}. The conflict was not resolved."
        ),
        "decisions": [],
        "action_items": [],
        "notes": (
            f"CONFLICTING DEADLINES: Database migration deadline stated as '{dl1}' "
            f"early in meeting, then revised to '{dl2}'. Conflict unresolved at end of meeting."
        ),
        "defect_type": "CONFLICTING_DEADLINE",
        "defect_description": (
            f"The same database migration task has two conflicting deadlines: '{dl1}' and '{dl2}'. "
            "The AI should flag the conflict rather than arbitrarily picking one."
        ),
    }
    return transcript, ground_truth


# ═══════════════════════════════════════════════════════════════════════════════
# DEFECT 4 — NO_DECISION
# Team explicitly defers; AI should NOT record this as a decision.
# ═══════════════════════════════════════════════════════════════════════════════

_DEFERRAL_PHRASES = [
    "Let's table this until we have more data.",
    "We're not ready to decide today — let's revisit next sprint.",
    "We explicitly agreed not to make this call yet.",
    "The decision will wait until after the architecture review.",
    "We'll need more information before committing to a direction.",
    "Let's punt on this one for now.",
    "No decision was made — we'll circle back in two weeks.",
    "We tabled the discussion for the next planning session.",
    "We agreed to defer this to the leadership team.",
    "Both options are still on the table; no decision reached today.",
]

_DEBATE_TOPICS = [
    ("whether to adopt Kubernetes for container orchestration",
     "the Kubernetes vs Docker Swarm decision"),
    ("whether to migrate the monolith to microservices",
     "the monolith migration decision"),
    ("whether to switch from REST to GraphQL for the public API",
     "the API design decision"),
    ("which cloud provider to use for the new region deployment",
     "the cloud provider selection"),
    ("whether to hire a dedicated DevOps engineer or upskill internally",
     "the hiring vs upskilling decision"),
    ("whether to delay the product launch to include feature X",
     "the launch timing decision"),
    ("which ORM to adopt for the new data layer",
     "the ORM selection"),
    ("whether to open-source the internal tooling",
     "the open-source decision"),
    ("how to restructure the support tiers",
     "the support tier redesign"),
    ("whether to sunset the legacy v1 API",
     "the v1 API deprecation decision"),
]

def _no_decision(idx: int) -> tuple[str, dict]:
    a, b = _name(idx, 0), _name(idx, 1)
    at, bt = _title(idx, 0), _title(idx, 1)
    date = _date(idx)
    topic = _topic(idx)
    debate, label = _DEBATE_TOPICS[idx % len(_DEBATE_TOPICS)]
    deferral = _DEFERRAL_PHRASES[idx % len(_DEFERRAL_PHRASES)]

    transcript = f"""Meeting: {topic}
Date: {date}

{a} ({at}) opened the meeting and introduced the main agenda item: a discussion about {debate}.

{b} ({bt}) presented the case for one approach, noting the performance benefits and team familiarity. {a} countered with concerns about cost, timeline, and migration risk.

After 40 minutes of discussion, neither side was able to reach a consensus. {a} summarised the situation: "{deferral}"

{b} agreed, adding that they would gather more metrics over the next two weeks before reconvening. Both committed to preparing a written recommendation for the follow-up meeting.

The meeting ended with no formal decision recorded on {label}."""

    ground_truth = {
        "title": topic,
        "date": date,
        "attendees": [a, b],
        "summary": (
            f"{a} and {b} held a structured discussion about {debate}. "
            "No decision was reached; the topic was explicitly deferred."
        ),
        "decisions": [],
        "action_items": [
            {
                "action": "Gather supporting metrics and prepare written recommendation",
                "owner": a,
                "deadline": "two weeks",
            },
            {
                "action": "Prepare written recommendation for follow-up meeting",
                "owner": b,
                "deadline": "two weeks",
            },
        ],
        "notes": f"Decision on {label} explicitly deferred. Follow-up meeting to be scheduled.",
        "defect_type": "NO_DECISION",
        "defect_description": (
            f"The team explicitly deferred {label}. "
            "The AI should NOT record a decision on this topic."
        ),
    }
    return transcript, ground_truth


# ═══════════════════════════════════════════════════════════════════════════════
# DEFECT 5 — IMPLICIT_ACTION
# Vague, uncommitted statements; AI should NOT create formal action items.
# ═══════════════════════════════════════════════════════════════════════════════

_VAGUE_STATEMENTS = [
    ("It would probably be helpful to add a tooltip to the export button.",
     "vague UX suggestion with no assignment"),
    ("We should look into whether GraphQL would work better for our needs.",
     "speculative technical exploration, no commitment"),
    ("Someone might want to explore a weekly digest email option at some point.",
     "speculative feature idea, no owner or timeline"),
    ("It could be worth revisiting the onboarding flow later in the year.",
     "vague future consideration, no commitment"),
    ("We might benefit from a better alerting strategy down the road.",
     "general observation, no action assigned"),
    ("It would be nice to have better test coverage on the payments module eventually.",
     "aspirational quality comment, no formal commitment"),
    ("Maybe we should think about consolidating our logging tools.",
     "speculative tooling idea, no owner"),
    ("At some point it would be good to document the internal APIs.",
     "vague documentation wish, no deadline or owner"),
    ("We could potentially look at caching to improve dashboard load times.",
     "exploratory performance idea, no assignment"),
    ("It might be worth exploring whether the current pricing model still makes sense.",
     "open-ended business consideration, no decision or owner"),
]

def _implicit_action(idx: int) -> tuple[str, dict]:
    a, b = _name(idx, 0), _name(idx, 1)
    at, bt = _title(idx, 0), _title(idx, 1)
    date = _date(idx)
    topic = _topic(idx)
    vague_stmt, vague_label = _VAGUE_STATEMENTS[idx % len(_VAGUE_STATEMENTS)]

    transcript = f"""Meeting: {topic}
Date: {date}

{a} ({at}) opened the meeting by reviewing recent customer support tickets and usage analytics.

{b} ({bt}) noted that three recurring complaints pointed to a friction point in the user journey. The team spent time reviewing the UX flow and discussing possible improvements.

During the review, {a} mentioned in passing: "{vague_stmt}" Neither {b} nor {a} followed up to assign ownership, set a deadline, or add it to the sprint backlog.

{b} raised a separate confirmed action item: she committed to drafting a summary of the customer complaints for the next product review by end of week.

The meeting ended with one formal commitment recorded."""

    ground_truth = {
        "title": topic,
        "date": date,
        "attendees": [a, b],
        "summary": (
            f"{a} and {b} reviewed customer support tickets and discussed UX friction points. "
            f"One formal action item was assigned. An informal observation was noted but not committed."
        ),
        "decisions": [],
        "action_items": [
            {
                "action": "Draft summary of customer complaints for product review",
                "owner": b,
                "deadline": "end of week",
            }
        ],
        "notes": (
            f"Informal observation by {a}: \"{vague_stmt}\" "
            f"This is a {vague_label} — not a formal action item."
        ),
        "defect_type": "IMPLICIT_ACTION",
        "defect_description": (
            f"The statement '{vague_stmt[:60]}…' is {vague_label}. "
            "The AI should NOT generate a formal action item from it."
        ),
    }
    return transcript, ground_truth


# ═══════════════════════════════════════════════════════════════════════════════
# Generator registry
# ═══════════════════════════════════════════════════════════════════════════════

_GENERATORS = {
    "missing_attendee": _missing_attendee,
    "ambiguous_owner": _ambiguous_owner,
    "conflicting_deadline": _conflicting_deadline,
    "no_decision": _no_decision,
    "implicit_action": _implicit_action,
}


class CaseGenerator:
    """Write synthetic audit cases to audit_cases/."""

    def __init__(
        self,
        transcripts_dir: Path = TRANSCRIPTS_DIR,
        ground_truth_dir: Path = GROUND_TRUTH_DIR,
    ) -> None:
        self.transcripts_dir = transcripts_dir
        self.ground_truth_dir = ground_truth_dir

    def _write_case(self, transcript_id: str, transcript: str, ground_truth: dict) -> None:
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)

        (self.transcripts_dir / f"{transcript_id}.txt").write_text(
            transcript, encoding="utf-8"
        )
        with open(self.ground_truth_dir / f"{transcript_id}.json", "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, indent=2, ensure_ascii=False)

    def generate_defect_type(self, defect_type: str, count: int = 10) -> list[str]:
        """Generate *count* cases for a single defect type. Returns list of IDs."""
        gen = _GENERATORS[defect_type]
        ids: list[str] = []
        prefix = defect_type.replace("_", "-")
        for i in range(count):
            transcript_id = f"{prefix}-{i + 1:03d}"
            transcript, ground_truth = gen(i)
            # Stamp the ground truth with its ID
            ground_truth["transcript_id"] = transcript_id
            self._write_case(transcript_id, transcript, ground_truth)
            ids.append(transcript_id)
        return ids

    def generate_all(self, count_per_type: int = 2) -> dict[str, list[str]]:
        """Generate cases for all 5 defect types. Returns {defect_type: [ids]}."""
        result: dict[str, list[str]] = {}
        for defect_type in _GENERATORS:
            result[defect_type] = self.generate_defect_type(defect_type, count_per_type)
        return result

    @staticmethod
    def list_defect_types() -> list[str]:
        return list(_GENERATORS.keys())


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    requested = sys.argv[1] if len(sys.argv) > 1 else "all"
    gen = CaseGenerator()

    if requested == "all":
        results = gen.generate_all()
        total = sum(len(v) for v in results.values())
        print(f"Generated {total} cases across {len(results)} defect types:")
        for dt, ids in results.items():
            print(f"  {dt}: {len(ids)} cases")
    elif requested in _GENERATORS:
        ids = gen.generate_defect_type(requested)
        print(f"Generated {len(ids)} cases for '{requested}':")
        for tid in ids:
            print(f"  {tid}")
    else:
        print(f"Unknown defect type '{requested}'. Available: all, {', '.join(_GENERATORS)}")
        sys.exit(1)
