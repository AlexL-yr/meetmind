# MeetingTruth

AI ethics audit system for meeting summarization. Built on top of MeetMind's multi-agent foundation.

**MeetMind** (original): routes user input to a chat agent or a Gemini-powered meeting summarizer.  
**MeetingTruth** (new): audits that Gemini meeting agent for hallucinations using Claude as the top-level orchestrator and ChromaDB + sentence-transformers as the ground-truth RAG layer.

---

## Architecture

### Original MeetMind pipeline (unchanged)

```
User Input
    ↓
Router Agent (Intent Recognition — Gemini)
    ├── Chat Agent    → Conversational response with memory
    └── Meeting Agent → Structured MeetingSummary (Gemini)
```

### MeetingTruth audit layer (new)

```
Transcript (defective input)
    ↓
Audit Agent (Claude — top-level orchestrator)
    ├── MCP tool: get_ground_truth   → ChromaDB RAG retrieval
    ├── Meeting Agent (Gemini)       → AI output under audit
    ├── MCP tool: compare_outputs    → field-by-field diff
    ├── Claude classifies each flag  → HallucinationType + severity + ethical_risk
    └── MCP tool: write_audit_log    → AuditResult → JSONL + CSV

Judge Agent (Gemini — secondary validation, advisory only)
    └── Secondary hallucination flags → "CANDIDATE FLAGS — FOR HUMAN REVIEW"
```

### Component responsibilities

| Component | Model | Role |
|---|---|---|
| `AuditAgent` | Claude (`claude-sonnet-4-20250514`) | Top-level orchestrator, hallucination classifier |
| `MeetingAgent` | Gemini (`gemini-2.0-flash`) | Subject under audit — do not modify its prompts |
| `JudgeAgent` | Gemini (`gemini-2.0-flash`) | Secondary validation pass (advisory) |
| ChromaDB + `all-MiniLM-L6-v2` | local / free | Ground-truth RAG (no API key) |
| MCP server | — | Exposes audit tools for Claude Desktop / MCP clients |

---

## Hallucination Types

| Type | Description |
|---|---|
| `FABRICATION` | AI invented something not present in the transcript |
| `OMISSION` | AI missed something clearly stated |
| `MISATTRIBUTION` | AI assigned an action/decision to the wrong person |
| `FALSE_DECISION` | AI marked a deferred discussion as decided |
| `INFERRED_TASK` | AI created a formal action item from a vague statement |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and GOOGLE_API_KEY
```

### 3. Generate the 50 synthetic test cases

```bash
python run_audit.py --generate
```

### 4. (Optional) Index ground truth into ChromaDB

```bash
python run_audit.py --index
```

### 5. Run the audit

```bash
# Audit all 50 cases
python run_audit.py --cases all

# Audit a specific defect type
python run_audit.py --cases missing_attendee

# Audit multiple defect types
python run_audit.py --cases missing_attendee,no_decision

# Print the aggregated summary table
python run_audit.py --report
```

### 6. Run original MeetMind CLI / API (unchanged)

```bash
python run_agent.py       # interactive CLI
python run_service.py     # FastAPI on :8000
```

---

## Audit Output

### `audit_cases/results/audit_log.jsonl`
One JSON object per audited case. Contains full `AuditResult` with all
`HallucinationFlag` details, scores, and risk classification.

### `audit_cases/results/audit_results.csv`

| Column | Description |
|---|---|
| `transcript_id` | e.g. `missing-attendee-003` |
| `defect_type` | one of the 5 defect types |
| `hallucination_score` | 0.0 – 1.0 |
| `misattribution_count` | count of MISATTRIBUTION flags |
| `missing_items_count` | count of OMISSION flags |
| `fabrication_count` | count of FABRICATION flags |
| `overall_risk` | `high` / `medium` / `low` |

---

## MCP Server (Claude Desktop integration)

The MCP server exposes all four audit tools as standard MCP tools:

```bash
python -m src.mcp.server
```

Tools available:
- `get_ground_truth(transcript_id)` — retrieve expected output from RAG
- `compare_outputs(ground_truth, ai_output)` — field-by-field diff
- `write_audit_log(audit_result)` — persist result to JSONL
- `get_audit_summary()` — aggregate statistics across all audits

---

## Test Cases (50 total)

The case generator creates 10 transcripts for each of the 5 defect types.
Each case includes a raw `.txt` transcript and a `.json` ground truth.

| Defect Type | Description |
|---|---|
| `MISSING_ATTENDEE` | Transcript only mentions 2 people; AI may hallucinate a 3rd |
| `AMBIGUOUS_OWNER` | Owner explicitly unresolved ("someone will handle it") |
| `CONFLICTING_DEADLINE` | Same task mentioned with two different deadlines |
| `NO_DECISION` | Team explicitly defers; AI may mark as decided |
| `IMPLICIT_ACTION` | Vague statement ("we should look into…"); AI may formalise it |

---

## Project Structure

```
meetingtruth/
├── src/
│   ├── agent/
│   │   ├── router_agent.py         # Intent routing (Gemini)
│   │   ├── chat_agent.py           # Conversational agent with memory
│   │   ├── meeting_agent.py        # Meeting summarizer (Gemini) — audit subject
│   │   ├── audit_agent.py          # Claude-powered audit orchestrator
│   │   ├── judge_agent.py          # Gemini secondary validation pass
│   │   ├── factory.py              # Agent factory helpers
│   │   └── prompts.py              # All system prompts
│   ├── rag/
│   │   ├── indexer.py              # ChromaDB indexer (sentence-transformers)
│   │   └── retriever.py            # Semantic retrieval
│   ├── mcp/
│   │   ├── server.py               # FastMCP server
│   │   └── tools/
│   │       ├── get_ground_truth.py
│   │       ├── write_audit_log.py
│   │       ├── compare_outputs.py
│   │       └── get_audit_summary.py
│   ├── synthesis/
│   │   └── case_generator.py       # 50 synthetic test transcripts
│   ├── core/
│   │   ├── config.py               # Settings (Claude + Gemini + Chroma)
│   │   └── llm.py                  # get_claude_client(), get_llm()
│   ├── memory/
│   │   └── manager.py              # Conversation memory
│   ├── schema/
│   │   ├── meeting.py              # MeetingSummary
│   │   ├── router.py               # RouterDecision
│   │   └── audit.py                # AuditResult, HallucinationFlag
│   └── session/
│       └── SessionManager.py
├── audit_cases/
│   ├── raw_transcripts/            # 50 × .txt  (generated)
│   ├── ground_truth/               # 50 × .json (generated)
│   └── results/                    # audit_log.jsonl + audit_results.csv
├── run_agent.py                    # Original MeetMind CLI
├── run_service.py                  # Original FastAPI service
├── run_audit.py                    # Batch audit runner
├── .env.example
└── pyproject.toml
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (Claude) | ✅ for auditing |
| `GOOGLE_API_KEY` | Google AI Studio (Gemini, free tier) | ✅ |
| `MODEL_NAME_CLAUDE` | Claude model (default: `claude-sonnet-4-20250514`) | ❌ |
| `MODEL_NAME_GEMINI` | Gemini model (default: `gemini-2.0-flash`) | ❌ |
| `LLM_TEMPERATURE` | Shared temperature (default: `0.7`) | ❌ |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path (default: `./chroma_db`) | ❌ |

---

## Tech Stack

- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude API (audit orchestration)
- [LangChain + Google Gemini](https://github.com/langchain-ai/langchain-google) — meeting agent
- [ChromaDB](https://www.trychroma.com/) — local vector store (no API key)
- [sentence-transformers](https://www.sbert.net/) — local embeddings (`all-MiniLM-L6-v2`)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) — audit tool server
- [FastAPI](https://fastapi.tiangolo.com/) — REST API
- [LangGraph](https://github.com/langchain-ai/langgraph) — chat agent ReAct loop

## License

MIT
