from functools import lru_cache
from typing import Optional,Literal
from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict

LLMProvider = Literal["google"]

PROVIDER_BASE_URLS ={
  "google": "https://generativelanguage.googleapis.com/v1beta"
}

PROVIDER_DEFAULT_MODELS= {
  "google": "gemini-2.0-flash"
}

class Settings(BaseSettings):

  model_config= SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore"
  )
  llm_provider: LLMProvider = Field(default="google")
  google_api_key: str = Field(default="")

  llm_model: str = Field(default="")
  llm_temperature: float = Field(default=0.7,ge=0.0,le=1.0)

  # Claude / Anthropic
  anthropic_api_key: str = Field(default="")
  model_name_claude: str = Field(default="claude-sonnet-4-20250514")
  model_name_gemini: str = Field(default="gemini-2.0-flash")

  # ChromaDB
  chroma_persist_dir: str = Field(default="./chroma_db")

  api_host: str = Field(default="0.0.0.0")
  api_port: int = Field(default=8000,ge=0,le=65535)
  api_key: Optional[str] = Field(default=None)
  require_auth: bool = Field(default=False)

def get_effective_llm_config(seetings: Settings, provider: Optional[str] = None) -> tuple[str,str,str]:
  """Return the effective LLM configuration for the given provider."""
  provider = provider or seetings.llm_provider
  base_url = PROVIDER_BASE_URLS[provider]
  model = (seetings.llm_model or "").strip() or PROVIDER_DEFAULT_MODELS.get(provider, PROVIDER_DEFAULT_MODELS["google"])
  key_map = {
    "google": seetings.google_api_key
  }
  api_key = key_map.get(provider) or seetings.api_key
  return api_key or "",base_url,model

@lru_cache
def get_settings() -> Settings:
  """Avoid reloading the settings every time."""
  return Settings()
