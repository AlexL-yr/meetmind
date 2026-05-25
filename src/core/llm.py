"""LLM clients for Claude (Anthropic) and Gemini (Google)."""
from functools import lru_cache
from typing import Optional
from anthropic import Anthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import get_effective_llm_config, get_settings


@lru_cache
def get_llm(provider: Optional[str] = None, temperature: Optional[float] = None, model: Optional[str] = None) -> ChatGoogleGenerativeAI:
    """Return the Gemini LangChain LLM (backward-compatible singleton)."""
    settings = get_settings()
    api_key, _base, default_model = get_effective_llm_config(settings, provider)
    return ChatGoogleGenerativeAI(
        model=model or settings.model_name_gemini or default_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        google_api_key=api_key,
    )


@lru_cache(maxsize=1)
def get_claude_client() -> Anthropic:
    """Return the Anthropic client singleton."""
    settings = get_settings()
    return Anthropic(api_key=settings.anthropic_api_key)


def get_claude_model_name() -> str:
    """Return the configured Claude model name."""
    return get_settings().model_name_claude


def get_gemini_model_name() -> str:
    """Return the configured Gemini model name."""
    return get_settings().model_name_gemini
