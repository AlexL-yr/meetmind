"""New LangGraph Agent.
  pip install langgraph-cli && langgraph new my-agent
This module defines a custom graph.
"""

from .graph import graph
from .factory import create_all_agents
__all__ = ["graph", "create_all_agents"]
