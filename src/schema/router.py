from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
class Intent(str, Enum):
  CHAT = "chat"
  METTING = "meeting"
  UNKNOWN = "unknown"

class RouterDecision(BaseModel):
  """
  main agent 
  """
  model_config = ConfigDict(use_enum_values=True)
  intent: Intent = Field(
    ...,
    description="The intent of the user message"
  )
  confidence: float = Field(
    ...,
    ge=0.0,
    le=1.0,
    description="The confidence of the intent"
  )

  reasoning: str = Field(
    ...,
    description="The reasoning for the intent"
  )
  extracted_info: dict = Field(
    default=None,
    description="The extracted information from the user message"
  )
  