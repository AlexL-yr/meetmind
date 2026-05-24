import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock

with patch("langchain_community.memory.ConversationSummaryBufferMemory", create=True):
    with patch("src.core.llm.get_llm", create=True):
        from src.session.SessionManager import SessionManager


# 2. 注意：这里的 @patch 路径必须全部换成 src.session.SessionManager ！！！
@patch("src.session.SessionManager.get_memory_manager")
def test_session_manager_init(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager(timeout_hours=24)
    assert manager is not None
    assert manager.get_session_count() == 0


@patch("src.session.SessionManager.get_memory_manager")
def test_create_session_auto_id(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager()
    session_id = manager.create_session()
    assert session_id is not None
    assert len(session_id) > 0
    assert manager.get_session_count() == 1


@patch("src.session.SessionManager.get_memory_manager")
def test_create_session_custom_id(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager()
    session_id = manager.create_session("my_session")
    assert session_id == "my_session"
    assert manager.get_session_count() == 1


@patch("src.session.SessionManager.get_memory_manager")
def test_create_session_duplicate(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager()
    sid1 = manager.create_session("test_session")
    assert sid1 == "test_session"
    assert manager.get_session_count() == 1
    sid2 = manager.create_session("test_session")
    assert sid2 == "test_session"
    assert manager.get_session_count() == 1


@patch("src.session.SessionManager.get_memory_manager")
def test_get_session_memory(mock_get_mem):
    mock_mem = MagicMock()
    mock_get_mem.return_value = mock_mem
    manager = SessionManager()
    session_id = manager.create_session("test_session")
    memory = manager.get_session_memory(session_id)
    assert memory is not None
    memory = manager.get_session_memory("nonexistent")
    assert memory is None


@patch("src.session.SessionManager.get_memory_manager")
def test_get_or_create_session(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager()
    sid1, mem1 = manager.get_or_create_session(None)
    assert sid1 is not None
    assert mem1 is not None
    assert manager.get_session_count() == 1
    sid2, mem2 = manager.get_or_create_session("new_user")
    assert sid2 == "new_user"
    assert manager.get_session_count() == 2
    sid3, mem3 = manager.get_or_create_session("new_user")
    assert sid3 == "new_user"
    assert manager.get_session_count() == 2


@patch("src.session.SessionManager.get_memory_manager")
def test_update_activity(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager()
    session_id = manager.create_session("test_session")
    session_data = manager._sessions[session_id]
    assert session_data.message_count == 0
    t1 = session_data.last_active
    manager.update_activity(session_id)
    assert session_data.message_count == 1
    assert session_data.last_active >= t1


@patch("src.session.SessionManager.get_memory_manager")
def test_cleanup_expired(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager(timeout_hours=1)
    sid1 = manager.create_session("session_1")
    sid2 = manager.create_session("session_2")
    assert manager.get_session_count() == 2
    manager._sessions[sid1].last_active = datetime.now() - timedelta(hours=2)
    cleaned_count = manager.cleanup_expired()
    assert cleaned_count == 1
    assert manager.get_session_count() == 1
    assert sid2 in manager._sessions
    assert sid1 not in manager._sessions


@patch("src.session.SessionManager.get_memory_manager")
def test_cleanup_thread_lifecycle(mock_get_mem):
    mock_get_mem.return_value = MagicMock()
    manager = SessionManager(cleanup_interval=1)
    assert manager._running is False
    assert manager._cleanup_thread is None
    manager.start_cleanup_thread()
    assert manager._running is True
    assert manager._cleanup_thread is not None
    assert manager._cleanup_thread.is_alive()
    first_thread = manager._cleanup_thread
    manager.start_cleanup_thread()
    assert manager._cleanup_thread is first_thread
    manager.stop_cleanup_thread()
    assert manager._running is False
    assert manager._cleanup_thread is None