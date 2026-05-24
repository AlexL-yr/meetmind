import pytest
from unittest.mock import patch,MagicMock
from src.core.config import Settings, get_effective_llm_config
def test_settings_default(monkeypatch):
  monkeypatch.setenv("GOOGLE_API_KEY", "mock_key")
  from src.core.config import Settings
  settings = Settings()
  assert settings.api_host == "0.0.0.0"
  assert settings.api_port == 8000

def test_effective_llm_config():
  from src.core.config import get_effective_llm_config, PROVIDER_BASE_URLS, PROVIDER_DEFAULT_MODELS
  mock_instance = MagicMock()
  mock_instance.llm_provider = "google"
  mock_instance.base_url = "https://generativelanguage.googleapis.com/v1beta"
  mock_instance.llm_model = ""
  mock_instance.google_api_key= "AImy-super-secret-agent-key-2026"

  api_key,base_url,model = get_effective_llm_config(mock_instance,"google")
  assert "AI" in api_key
  assert "gemini-3.1-flash-lite" in model
  assert "v1beta" in base_url
