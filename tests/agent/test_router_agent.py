"""Router Agent Tests"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# 1. 强制注入项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. 【核心】在导入前注入所有可能导致崩溃的外部依赖模块
mock_core = MagicMock()
mock_llm_instance = MagicMock()
mock_core.get_llm.return_value = mock_llm_instance
sys.modules["src.core"] = mock_core

# 垫平 schema 的相对导入错误
mock_schema = MagicMock()
sys.modules["src.schema"] = mock_schema

# 3. 此时安全导入目标类和变量
from src.agent.router_agent import RouterAgent
from src.agent.prompts import ROUTER_USER_TEMPLATE


def test_router_agent_init():
    """Test RouterAgent initialization"""
    agent = RouterAgent()
    assert agent is not None
    assert agent._llm is mock_llm_instance


def test_router_agent_with_custom_llm():
    """Test using custom LLM"""
    custom_llm = MagicMock()
    agent = RouterAgent(llm=custom_llm)
    assert agent._llm is custom_llm


def test_router_agent_has_decide_method():
    """Test presence of decide methods"""
    agent = RouterAgent()
    assert hasattr(agent, "decide")
    assert hasattr(agent, "adecide")


def test_router_agent_with_structured_output():
    """Test that with_structured_output is called"""
    custom_llm = MagicMock()
    custom_llm.with_structured_output.return_value = MagicMock()

    agent = RouterAgent(llm=custom_llm)
    custom_llm.with_structured_output.assert_called_once()


def test_router_decide_sync():
    """Test synchronous decision making"""
    mock_structured_agent = MagicMock()
    mock_decision = MagicMock()
    mock_decision.intent = "chat"
    mock_decision.confidence = 0.95
    mock_structured_agent.invoke.return_value = mock_decision

    custom_llm = MagicMock()
    custom_llm.with_structured_output.return_value = mock_structured_agent

    with patch("src.agent.router_agent.ROUTER_USER_TEMPLATE") as mock_template:
        mock_template.format.return_value = "Please analyze: Hello"

        agent = RouterAgent(llm=custom_llm)
        result = agent.decide("Hello")

        assert result.intent == "chat"
        assert result.confidence == 0.95