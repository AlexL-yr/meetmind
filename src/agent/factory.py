from typing import Optional, Tuple
from ..session import get_session_manager, SessionManager
from ..session import get_session_manager
from ..session.SessionManager import SessionManager
from ..core import get_llm
from ..memory import MemoryManager, get_memory_manager
from ..agent.router_agent import RouterAgent
from ..agent.chat_agent import ChatAgent
from ..agent.meeting_agent import MeetingAgent
# Global Agent Instances (Stateless)
_router = None
_meeting = None


def create_router_agent(llm=None) -> RouterAgent:
    """
    Create Router Agent.
    
    Args:
        llm: Optional LLM instance.
        
    Returns:
        RouterAgent: Router Agent instance.
    """
    global _router
    if _router is None:
        _router = RouterAgent(llm=llm)
    return _router


def create_chat_agent(llm=None, tools=None, memory: Optional[MemoryManager] = None) -> ChatAgent:
    """
    Create Chat Agent.
    
    Each call creates a new instance because ChatAgent contains session memory state.
    
    Args:
        llm: Optional LLM instance.
        tools: Optional list of tools.
        memory: Optional memory manager instance.
        
    Returns:
        ChatAgent: A newly created Chat Agent instance.
    """
    return ChatAgent(llm=llm, tools=tools, memory=memory)


def create_meeting_agent(llm=None) -> MeetingAgent:
    """
    Create Meeting Agent.
    
    Args:
        llm: Optional LLM instance.
        
    Returns:
        MeetingAgent: Meeting Agent instance.
    """
    global _meeting
    if _meeting is None:
        _meeting = MeetingAgent(llm=llm)
    return _meeting

def create_all_agents(with_memory: bool = True, memory_llm=None) -> tuple:
    """
    Convenience function to create all Agents (Backward compatibility interface).
    
    Note: Agents created by this method share the same memory instance, 
    which does not support multi-session isolation.
    If multi-session isolation is required, please use create_agents_with_session.
    
    Args:
        with_memory: Whether to enable memory functionality for Chat Agent.
        memory_llm: LLM instance used for memory summarization.
        
    Returns:
        tuple: (router, chat, meeting) Three Agent instances.
    """
    memory = None
    if with_memory:
        memory = get_memory_manager(llm=memory_llm)
        
    router = create_router_agent()
    chat = create_chat_agent(memory=memory)
    meeting = create_meeting_agent()
    
    return router, chat, meeting

def create_agents_with_session(
        llm = None,
        session_id: Optional[str] = None,
        session_manager: Optional[SessionManager] = None,
) -> Tuple[RouterAgent, ChatAgent, MeetingAgent, str]:
    """
    Create agents with session support.

    Args:
        llm: Optional LLM instance
        session_id: Optional session identifier
        session_manager: Optional session manager instance

    Returns:
        tuple: (router, chat, meeting, session_id)
            router:     Router Agent [stateless]
            chat:       Chat Agent   [with independent memory]
            meeting:    Meeting Agent [stateless]
            session_id: The actual session identifier used
    """
    # Get or create session
    if session_manager is None:
        session_manager = get_session_manager()

    session_id, memory = session_manager.get_or_create_session(session_id)

    # Create Agents
    router  = create_router_agent(llm=llm)
    chat    = create_chat_agent(llm=llm, memory=memory)
    meeting = create_meeting_agent(llm=llm)

    return router, chat, meeting, session_id

def get_session_chat_agent(
        session_id: Optional[str] = None,
        llm=None,
        tools=None,
) -> Tuple[ChatAgent, str]:
    """
    Retrieve the ChatAgent for a given session.

    Convenience function: directly returns a session-aware ChatAgent.

    Args:
        session_id: Session identifier
        llm:        Optional LLM instance
        tools:      Optional list of tools

    Returns:
        tuple: (chat_agent, session_id)
    """
    session_manager = get_session_manager()
    session_id, memory = session_manager.get_or_create_session(session_id)
    chat = create_chat_agent(llm=llm, tools=tools, memory=memory)

    return chat, session_id