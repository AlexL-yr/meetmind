import warnings
# 1. 强行忽略所有来自 langchain_community 的 DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="importlib.*")

import os
import sys
# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import patch, MagicMock

# 2. Short-circuit LangChain community dependency during import collection
with patch("langchain_community.memory.ConversationSummaryBufferMemory", create=True):
    with patch("src.core.llm.get_llm", create=True):
        from src.memory.manager import MemoryManager, get_memory_manager

@pytest.fixture
def mock_dependencies():
    """Fixture to mock underlying LangChain memory instance in src.memory.manager"""
    with patch("src.memory.manager.ConversationSummaryBufferMemory", create=True) as mock_cls:
        mock_ins = MagicMock()
        mock_cls.return_value = mock_ins
        yield mock_ins

# ==================== Test Cases ====================

def test_memory_manager_init(mock_dependencies):
    """Test MemoryManager initialization"""
    manager = MemoryManager(max_token_limit=1000)
    assert manager is not None
    assert manager._max_token_limit == 1000
    assert manager._memory_key == "history"

def test_memory_manager_custom_key(mock_dependencies):
    """Test custom memory_key"""
    manager = MemoryManager(memory_key="chat_history")
    assert manager._memory_key == "chat_history"

def test_add_user_message(mock_dependencies):
    """Test adding a user message to memory"""
    manager = MemoryManager()
    manager.add_user_message("Hello AI")
    mock_dependencies.chat_memory.add_user_message.assert_called_once_with("Hello AI")

def test_add_ai_message(mock_dependencies):
    """Test adding an AI message to memory"""
    manager = MemoryManager()
    manager.add_ai_message("Hello Human")
    mock_dependencies.chat_memory.add_ai_message.assert_called_once_with("Hello Human")

def test_get_history(mock_dependencies):
    """Test retrieving conversation history list"""
    from langchain_core.messages import HumanMessage, AIMessage
    mock_messages = [HumanMessage(content="Hi"), AIMessage(content="Hello")]
    mock_dependencies.load_memory_variables.return_value = {"history": mock_messages}
    
    manager = MemoryManager(memory_key="history")
    history = manager.get_history()
    
    assert len(history) == 2
    assert history[0].content == "Hi"

def test_clear_memory(mock_dependencies):
    """Test clearing all conversation memory"""
    manager = MemoryManager()
    manager.clear()
    mock_dependencies.clear.assert_called_once()

def test_get_context_formatting(mock_dependencies):
    """Test that get_context formats messages into a clean raw string"""
    from langchain_core.messages import HumanMessage, AIMessage
    mock_messages = [
        HumanMessage(content="Do you code?"),
        AIMessage(content="Yes I do.")
    ]
    mock_dependencies.load_memory_variables.return_value = {"history": mock_messages}
    
    manager = MemoryManager()
    context = manager.get_context()
    
    assert context == "User: Do you code?\nAI: Yes I do."

def test_get_context_empty(mock_dependencies):
    """Test that get_context returns empty string when history is empty"""
    mock_dependencies.load_memory_variables.return_value = {"history": []}
    
    manager = MemoryManager()
    assert manager.get_context() == ""

def test_factory_function_get_memory_manager(mock_dependencies):
    """Test the factory helper initialization and kwargs forwarding"""
    manager = get_memory_manager(max_token_limit=500, memory_key="custom")
    assert isinstance(manager, MemoryManager)
    assert manager._max_token_limit == 500
    assert manager._memory_key == "custom"