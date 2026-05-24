"""Chat Schema Tests"""
import pytest
from pydantic import ValidationError
from src.schema.chat import ChatRequest, ChatResponse

def test_chat_request_creation():
    """Test creating ChatRequest"""
    req = ChatRequest(message="Hello")
    assert req.message == "Hello"
    assert req.session_id is None

def test_chat_request_with_session_id():
    """Test ChatRequest with session_id"""
    req = ChatRequest(message="Hello", session_id="abc123")
    assert req.message == "Hello"
    assert req.session_id == "abc123"

def test_chat_request_message_required():
    """Test that message field is required"""
    with pytest.raises(ValidationError):
        ChatRequest()