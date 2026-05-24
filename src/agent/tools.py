from datetime import datetime
from langchain_core.tools import tool

# Define tool functions available for the Chat Agent.
# Create tools that can be called by the Agent using LangChain's @tool decorator.

@tool
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """
    Get the current date and time.
    
    Args:
        timezone: Timezone name, defaults to Asia/Shanghai.
        
    Returns:
        str: Formatted date and time string.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """
    Calculate a mathematical expression.
    """
    try:
        # Only allow safe characters to prevent injection attacks
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: Expression contains disallowed characters"
        return str(eval(expression))
    except Exception as e:
        return f"Calculation Error: {e}"


@tool
def echo(message: str) -> str:
    """
    Echo the message back.
    
    Returns the input message exactly as it is, used for testing and demonstration.
    
    Args:
        message: Any string.
        
    Returns:
        str: The identical input string.
    """
    return message


def get_default_tools():
    """
    Get the list of default tools.
    
    Returns:
        list: A list containing all default tools.
    """
    return [get_current_time, calculator, echo]