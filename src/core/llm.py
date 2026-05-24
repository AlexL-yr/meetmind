"""
LLM module for the agent.
"""
from functools import lru_cache
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from .config import get_effective_llm_config, get_settings

@lru_cache
def get_llm(provider: Optional[str] = None, temperature: Optional[float] = None, model: Optional[str] = None) ->ChatGoogleGenerativeAI:
  """ 
  get the LLM instance for the agent.
  """
  
  settings = get_settings()
  api_key, api_base, default_model = get_effective_llm_config(settings, provider)
  return ChatGoogleGenerativeAI(
    model = model or default_model,
    temperature= temperature or settings.llm_temperature,
    api_key= api_key
  )
  

