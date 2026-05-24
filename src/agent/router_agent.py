from typing import Optional
from ..core import get_llm
from ..schema import RouterDecision
from .prompts import ROUTER_SYSTEM_PROMPT, ROUTER_USER_TEMPLATE

class RouterAgent:
    """
    Responsible for intent recognition, achieving automatic routing via LLM + with_structured_output.
    Determines user intent based on input (casual conversation or meeting minutes summary), 
    and returns a structured routing decision.
    """

    def __init__(self, llm=None):
        """
        Initialize Router Agent

        Args:
            llm: Optional LangChain LLM instance, defaults to global configuration.
        """
        # Action: Initialize LLM and wrap it using the with_structured_output method,
        # forcing it to output a structured RouterDecision object.
        self._llm = llm or get_llm()
        self._agent = self._llm.with_structured_output(RouterDecision)

    def decide(self, user_input: str) -> RouterDecision:
        """
        Synchronously decide user intent.

        Args:
            user_input: Text input from the user.

        Returns:
            RouterDecision: Structured routing decision result.
        """
        user_prompt = ROUTER_USER_TEMPLATE.format(user_input=user_input)
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return self._agent.invoke(messages)

    async def adecide(self, user_input: str) -> RouterDecision:
        """
        Asynchronously decide user intent.

        Args:
            user_input: Text input from the user.

        Returns:
            RouterDecision: Structured routing decision result.
        """
        user_prompt = ROUTER_USER_TEMPLATE.format(user_input=user_input)
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        return await self._agent.ainvoke(messages)


def create_router_agent(**kwargs) -> RouterAgent:
    """
    Factory function to create a Router Agent.

    Args:
        **kwargs: Parameters passed to RouterAgent.

    Returns:
        RouterAgent: Router Agent instance.
    """
    return RouterAgent(**kwargs)