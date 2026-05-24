from typing import Optional
from ..core import get_llm
from ..schema.meeting import MeetingSummary
from .prompts import MEETING_SYSTEM_PROMPT, MEETING_USER_TEMPLATE

class MeetingAgent:
    """
    Meeting Minutes Summary Agent
    
    Extracts key information from unorganized meeting content 
    and outputs structured MeetingSummary results.
    """

    def __init__(self, llm=None):
        """
        Initialize Meeting Agent.
        
        Args:
            llm: Optional LangChain LLM instance. Defaults to global configuration.
        """
        self._llm = llm or get_llm()
        # Bound schema structure using with_structured_output for structured formatting
        self._agent = self._llm.with_structured_output(MeetingSummary)

    def summarize(self, meeting_content: str) -> MeetingSummary:
        """
        Synchronously summarize meeting contents.
        
        Args:
            meeting_content: Raw unstructured meeting text logs or transcripts.
            
        Returns:
            MeetingSummary: Structured data model matching schema layout.
        """
        user_prompt = MEETING_USER_TEMPLATE.format(meeting_content=meeting_content)
        messages = [
            {"role": "system", "content": MEETING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        return self._agent.invoke(messages)

    async def asummarize(self, meeting_content: str) -> MeetingSummary:
        """
        Asynchronously summarize meeting contents.
        
        Args:
            meeting_content: Raw unstructured meeting text logs or transcripts.
            
        Returns:
            MeetingSummary: Structured data model matching schema layout.
        """
        user_prompt = MEETING_USER_TEMPLATE.format(meeting_content=meeting_content)
        messages = [
            {"role": "system", "content": MEETING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        return await self._agent.ainvoke(messages)
    
def create_meeting_agent(**kwargs) -> MeetingAgent:
    """
    Factory function to create a Meeting Agent.

    Args:
        **kwargs: Parameters passed to MeetingAgent.

    Returns:
        MeetingAgent: Meeting Agent instance.
    """
    return MeetingAgent(**kwargs)