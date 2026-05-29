"""LLM clients — Ollama (meeting agent), Gemini (auditor), optionally Claude."""
from functools import lru_cache
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from .config import get_effective_llm_config, get_settings


def get_llm(provider: Optional[str] = None, temperature: Optional[float] = None, model: Optional[str] = None) -> ChatGoogleGenerativeAI:
    """Return a Gemini LangChain LLM instance."""
    settings = get_settings()
    api_key, _base, default_model = get_effective_llm_config(settings, provider)
    return ChatGoogleGenerativeAI(
        model=model or settings.model_name_gemini or default_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        google_api_key=api_key,
    )


def get_gemini_model_name() -> str:
    """Return the configured Gemini model name."""
    return get_settings().model_name_gemini


# ── Ollama (local — subject under audit) ──────────────────────────────────────

def get_ollama_llm(temperature: float = 0.1):
    """Return a ChatOllama instance pointing at the local Ollama server."""
    from langchain_ollama import ChatOllama
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
    )


# ── Optional Claude support (requires: pip install anthropic) ─────────────────

def get_claude_client():
    """Return an Anthropic client. Raises ImportError if anthropic is not installed."""
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise ImportError(
            "anthropic package is not installed. "
            "Install it with: pip install anthropic"
        ) from exc
    settings = get_settings()
    return Anthropic(api_key=settings.anthropic_api_key)


def get_claude_model_name() -> str:
    """Return the configured Claude model name."""
    return get_settings().model_name_claude
