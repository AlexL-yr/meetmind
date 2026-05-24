import uuid
import threading
import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from src.memory.manager import get_memory_manager

class SessionData:
    """
    Attributes:
        created_at: Session creation time
        last_active: Session last active time
        message_count: Message counter
        
    Note: Each SessionData object owns an independent MemoryManager,
    which ensures strict memory isolation between different sessions.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        # Create an independent memory manager for each session to isolate memory
        self.memory = get_memory_manager()
        # Record creation time for debugging and diagnostics
        self.created_at = datetime.now()
        # Record last active time to determine expiration status
        self.last_active = datetime.now()
        # Message counter for statistics and debugging
        self.message_count = 0


class SessionManager:
    def __init__(self, timeout_hours: int = 24, cleanup_interval: int = 3600):
        """
        Initialize Session Manager.
        """
        # Stores all active sessions, key is session_id, value is SessionData
        self._sessions: Dict[str, SessionData] = {}
        # Session expiration threshold, using timedelta for easy comparison
        self._timeout = timedelta(hours=timeout_hours)
        # Execution interval (seconds) for the background cleanup thread
        self._cleanup_interval = cleanup_interval
        # Background cleanup thread object, initialized as None
        self._cleanup_thread: Optional[threading.Thread] = None
        # Thread running flag controlling the startup and teardown of the background thread
        self._running = False

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session."""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionData(session_id)
            
        return session_id

    def get_session_memory(self, session_id: str):
        """Retrieve the memory manager for a specific session."""
        session = self._sessions.get(session_id)
        if session:
            return session.memory
        return None

    def get_or_create_session(self, session_id: Optional[str] = None) -> Tuple[str, object]:
        """Get an existing session or create a new one if it doesn't exist."""
        if not session_id:
            session_id = self.create_session()
        else:
            if session_id not in self._sessions:
                session_id = self.create_session(session_id)
                
        memory = self.get_session_memory(session_id)
        return session_id, memory

    def update_activity(self, session_id: str) -> None:
        """Update the active status time and increment message count of a session."""
        session = self._sessions.get(session_id)
        if session:
            session.last_active = datetime.now()
            session.message_count += 1

    def cleanup_expired(self) -> int:
        """Find and delete expired sessions, returning the count of cleaned sessions."""
        now = datetime.now()
        expired = [
            sid for sid, data in self._sessions.items()
            if now - data.last_active > self._timeout
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def get_session_count(self) -> int:
        """Get the number of currently active sessions."""
        return len(self._sessions)

    def start_cleanup_thread(self) -> None:
        """Start the background cleanup thread."""
        if self._running:
            return
            
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup_thread(self) -> None:
        """Set the stop flag and wait for the thread to exit."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join()
        self._cleanup_thread = None

    def _cleanup_loop(self) -> None:
        """
        1. Sleep for cleanup_interval
        2. Check the _running flag
        3. Execute the cleanup operation if still running
        4. Repeat step 1
        """
        while self._running:
            time.sleep(self._cleanup_interval)
            if self._running:
                count = self.cleanup_expired()
                if count > 0:
                    print(f"[SessionManager] Cleaned up {count} expired sessions")

# Global singleton instance
session_manager = SessionManager()