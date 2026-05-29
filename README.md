# MeetingTruth

AI ethics audit system for meeting summarization. A local LLM (LLaMA 3.1-8B) simulates a commercial meeting summarization product; Gemini acts as an independent auditor via the Model Context Protocol (MCP).

---

## Architecture

```
Transcript (with injected defect)
        │
        ▼
MeetingAgent — LLaMA 3.1-8B via Ollama      ← surrogate commercial system
        │  MeetingSummary (JSON)
        ▼
AuditAgent — Gemini flash-lite               ← independent auditor
        │
        │  MCP tool calls (stdio transport)
        ├─► get_ground_truth(id)    → file lookup
        ├─► compare_outputs(gt, ai) → field-by-field diff
        └─► write_audit_log(result) → AuditResult → JSONL

RAG (ChromaDB + all-MiniLM-L6-v2)
        └─► search_ground_truth(query) → cross-case semantic retrieval
```

### Component roles

| Component | Model | Role |
|---|---|---|
| `MeetingAgent` | LLaMA 3.1-8B (Ollama, local) | Subject under audit — simulates commercial meeting AI |
| `AuditAgent` | Gemini flash-lite | Independent auditor, calls MCP tools |
| `JudgeAgent` | Gemini flash-lite | Secondary validation pass (advisory only) |
| MCP server | — | Exposes audit tools via stdio transport |
| ChromaDB + `all-MiniLM-L6-v2` | local | Ground-truth RAG, cross-case similarity search |

---

## Hallucination Taxonomy

Five domain-specific types designed for meeting summarization:

| Type | Description |
|---|---|
| `FABRICATION` | AI invented content not present in the transcript |
| `OMISSION` | AI missed something clearly stated |
| `MISATTRIBUTION` | AI assigned an action/decision to the wrong person |
| `FALSE_DECISION` | AI marked a deferred discussion as decided |
| `INFERRED_TASK` | AI formalised a vague statement into an action item |

---

## Quick Start

### Prerequisites

- Python 3.13+
- [Ollama](https://ollama.ai) running locally with `llama3.1:8b` pulled
- Google AI Studio API key (free tier, 500 RPD)

```bash
ollama pull llama3.1:8b
```

### Install

```bash
pip install -e .
```

### Configure

```bash
cp .env.example .env
# Set GOOGLE_API_KEY in .env
```

### Run

```bash
# 1. Generate 10 synthetic test cases (2 per defect type)
python run_audit.py --generate

# 2. Index ground truth into ChromaDB (RAG)
python run_audit.py --index

# 3. Run all audits
python run_audit.py --cases all

# 4. RAG cross-case analysis
python run_audit.py --analyze

# 5. Generate visualizations (5 figures, 300 dpi)
python visualize_audit.py

# Run a specific defect type
python run_audit.py --cases missing_attendee
python run_audit.py --cases conflicting_deadline,no_decision

# Print aggregated summary
python run_audit.py --report
```

---

## Output Files

| Path | Description |
|---|---|
| `audit_cases/results/audit_log.jsonl` | Full `AuditResult` per case (append-only) |
| `audit_cases/results/audit_results.csv` | Summary table from last run |
| `audit_cases/results/ai_outputs/` | Raw LLaMA outputs (pre-audit) |
| `audit_cases/results/rag_analysis.json` | Cross-case RAG similarity data |
| `audit_cases/results/figures/` | fig1–fig5 (300 dpi PNG) |

---

## MCP Tools

The MCP server exposes four tools callable via any MCP client:

```bash
python -m src.mcp.server
```

| Tool | Description |
|---|---|
| `get_ground_truth(transcript_id)` | Exact lookup from ground-truth store |
| `compare_outputs(ground_truth, ai_output)` | Field-by-field structural diff |
| `write_audit_log(audit_result)` | Persist AuditResult to JSONL |
| `get_audit_summary()` | Aggregate stats across all audits |
| `search_ground_truth(query, n_results)` | Semantic similarity search via ChromaDB |

---

## Test Cases

10 synthetic cases (2 per defect type), each with a raw `.txt` transcript and a `.json` ground truth:

| Defect Type | What is injected |
|---|---|
| `missing_attendee` | Only 2 attendees mentioned; AI may hallucinate a third |
| `ambiguous_owner` | Ownership explicitly unresolved in transcript |
| `conflicting_deadline` | Same task mentioned with two different deadlines |
| `no_decision` | Team explicitly defers; AI may mark as decided |
| `implicit_action` | Vague statement ("we should look into…"); AI may formalise |

---

## Project Structure

```
meetingtruth/
├── src/
│   ├── agent/
│   │   ├── meeting_agent.py        # LLaMA surrogate (subject under audit)
│   │   ├── audit_agent.py          # Gemini auditor, MCP tool-use loop
│   │   ├── judge_agent.py          # Secondary validation (advisory)
│   │   └── prompts.py              # All system prompts
│   ├── mcp/
│   │   ├── server.py               # FastMCP server (stdio transport)
│   │   └── tools/                  # get_ground_truth, compare_outputs,
│   │                               #   write_audit_log, get_audit_summary,
│   │                               #   search_ground_truth
│   ├── rag/
│   │   ├── indexer.py              # ChromaDB indexer
│   │   ├── retriever.py            # Exact + semantic retrieval
│   │   └── singleton.py            # Shared retriever instance
│   ├── synthesis/
│   │   └── case_generator.py       # Synthetic transcript generator
│   ├── core/
│   │   ├── config.py               # Settings
│   │   └── llm.py                  # get_llm(), get_ollama_llm()
│   └── schema/
│       ├── meeting.py              # MeetingSummary
│       └── audit.py                # AuditResult, HallucinationFlag
├── audit_cases/
│   ├── raw_transcripts/            # 10 × .txt
│   ├── ground_truth/               # 10 × .json
│   └── results/                    # outputs (gitignored)
├── run_audit.py                    # Batch runner + analysis
├── visualize_audit.py              # 5 seaborn figures
└── pyproject.toml
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GOOGLE_API_KEY` | Google AI Studio key (Gemini auditor) | ✅ |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) | ❌ |
| `OLLAMA_MODEL` | Local model name (default: `llama3.1:8b`) | ❌ |
| `MODEL_NAME_GEMINI` | Gemini model (default: `gemini-3.1-flash-lite`) | ❌ |
| `CHROMA_PERSIST_DIR` | ChromaDB path (default: `./chroma_db`) | ❌ |

---

## Tech Stack

- [LangChain + Google Gemini](https://github.com/langchain-ai/langchain-google) — audit LLM
- [LangChain Ollama](https://github.com/langchain-ai/langchain-ollama) — local meeting agent
- [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) — MCP client for Gemini
- [MCP / FastMCP](https://modelcontextprotocol.io/) — audit tool server
- [ChromaDB](https://www.trychroma.com/) — local vector store
- [sentence-transformers](https://www.sbert.net/) — local embeddings (`all-MiniLM-L6-v2`)
- [seaborn / matplotlib](https://seaborn.pydata.org/) — academic visualizations

## License

MIT
