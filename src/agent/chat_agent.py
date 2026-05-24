from typing import Optional
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from ..core import get_llm
from ..memory import MemoryManager
from .prompts import CHAT_SYSTEM_PROMPT
from .tools import get_default_tools

class ChatAgent:
    def __init__(self, llm=None, tools=None, memory: Optional[MemoryManager] = None):
        """
        Initialize Chat Agent.
        
        Args:
            llm: Optional LangChain LLM instance.
            tools: Optional list of tools, defaults to get_default_tools().
            memory: Optional conversation memory manager.
        """
        self._llm = llm or get_llm()
        self._tools = tools or get_default_tools()
        self._memory = memory
        # Build ReAct Agent Graph
        self._graph = self._build_graph()

    def _build_graph(self):
        """Build ReAct Agent Graph"""
        return create_react_agent(
            model=self._llm,
            tools=self._tools,
            prompt=CHAT_SYSTEM_PROMPT,
        )

    def invoke(self, user_input: str) -> str:
        """
        Synchronously process user input.
        
        Args:
            user_input: Text input from the user.
            
        Returns:
            str: AI response content.
        """
        # If memory manager exists, save user message
        if self._memory:
            self._memory.add_user_message(user_input)
            
        # Build message list, including historical context
        messages = self._build_messages(user_input)
        
        result = self._graph.invoke({"messages": messages})
        reply = self._extract_reply(result)
        
        # If memory manager exists, save AI response
        if self._memory:
            self._memory.add_ai_message(reply)
            
        return reply

    async def ainvoke(self, user_input: str) -> str:
        """
        Asynchronously process user input.
        """
        # Note: Following standard async flow corresponding to the sync invoke method
        if self._memory:
            self._memory.add_user_message(user_input)
            
        messages = self._build_messages(user_input)
        result = await self._graph.ainvoke({"messages": messages})
        reply = self._extract_reply(result)
        
        if self._memory:
            self._memory.add_ai_message(reply)
            
        return reply

    def _build_messages(self, user_input: str) -> list:
        """
        Build message list, including historical context.
        
        Args:
            user_input: Current user input.
            
        Returns:
            list: List of messages containing historical history and current input.
        """
        messages = []
        
        # If memory manager exists, load conversation history
        if self._memory:
            history = self._memory.get_history()
            messages.extend(history)
            
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        return messages

    def _extract_reply(self, result: dict) -> str:
        """
        Extract response content from Agent result.
        
        Args:
            result: Agent execution result dictionary.
            
        Returns:
            str: Extracted response text.
        """
        messages = result.get("messages", [])
        # Reverse to find the last valid response content
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                return msg.content if isinstance(msg.content, str) else str(msg.content)
        return "Sorry, failed to generate a valid response."


def create_chat_agent(**kwargs) -> ChatAgent:
    """
    Factory function to create a Chat Agent.
    
    Args:
        **kwargs: Parameters passed to ChatAgent.
        
    Returns:
        ChatAgent: Chat Agent instance.
    """
    return ChatAgent(**kwargs)