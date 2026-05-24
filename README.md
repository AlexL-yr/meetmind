# MeetMind 🧠

An intelligent multi-agent system for meeting minutes generation and conversational AI, built with LangGraph and Google Gemini.

## Architecture

```
User Input
    ↓
Router Agent (Intent Recognition)
    ├── Chat Agent    → Conversational response with memory
    └── Meeting Agent → Structured meeting minutes (MeetingSummary)
```

## Features

- 🎯 **Automatic Intent Routing** — distinguishes between casual chat and meeting content
- 📋 **Structured Meeting Minutes** — extracts title, attendees, decisions, action items
- 🧠 **Conversation Memory** — retains context across turns with summary buffer
- 🌐 **REST API** — FastAPI service with `/chat` endpoint
- 🔄 **Session Management** — isolated memory per session

## Quick Start

### 1. Install dependencies

```bash
pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your GOOGLE_API_KEY
```

### 3. Run CLI

```bash
python run_agent.py
```

### 4. Run API Service

```bash
python run_service.py
# API docs: http://localhost:8000/docs
```

## API Usage

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Meeting minutes
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Today we discussed the Q3 roadmap. Attendees: Alice, Bob. Decision: adopt JWT auth. Action: Bob to complete API by May 30."}'
```

## API Response Example

```json
{
  "intent": "meeting",
  "confidence": 0.98,
  "response": "",
  "meeting": {
    "title": "Q3 Roadmap Review",
    "date": "2026-05-24",
    "attendees": ["Alice", "Bob"],
    "summary": "Discussed Q3 roadmap and authentication implementation.",
    "decisions": ["Adopt JWT authentication"],
    "action_items": [
      {
        "action": "Complete backend API",
        "owner": "Bob",
        "deadline": "2026-05-30"
      }
    ],
    "notes": ""
  }
}
```

## Project Structure

```
my-agent/
├── src/
│   ├── agent/              # Router, Chat, Meeting agents + factory
│   │   ├── router_agent.py
│   │   ├── chat_agent.py
│   │   ├── meeting_agent.py
│   │   ├── factory.py
│   │   └── prompts.py
│   ├── core/               # LLM configuration
│   │   └── llm.py
│   ├── memory/             # Conversation memory manager
│   │   └── manager.py
│   ├── schema/             # Pydantic models
│   │   ├── router.py       # RouterDecision
│   │   └── meeting.py      # MeetingSummary
│   └── session/            # Session management
│       └── SessionManager.py
├── tests/                  # Unit and integration tests
├── run_agent.py            # CLI entry point
├── run_service.py          # FastAPI service entry point
├── .env.example
└── pyproject.toml
```

## Tech Stack

- [LangGraph](https://github.com/langchain-ai/langgraph) — agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) — LLM framework
- [Google Gemini](https://ai.google.dev/) — LLM backend
- [FastAPI](https://fastapi.tiangolo.com/) — REST API
- [Pydantic](https://docs.pydantic.dev/) — structured output schema

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GOOGLE_API_KEY` | Google AI Studio API key | ✅ |
| `MODEL_NAME` | Gemini model name (default: `gemini-3.1-flash-lite`) | ❌ |
| `LLM_TEMPERATURE` | Model temperature (default: `0.7`) | ❌ |

## License

MIT
