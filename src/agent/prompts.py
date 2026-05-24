"""
Prompt Definitions

Defines system prompts and user templates used by various agents in the system.
"""
from datetime import datetime

_today = datetime.now().strftime("%Y-%m-%d")
# Main Router Agent System Prompt: Used for intent recognition
ROUTER_SYSTEM_PROMPT = """You are an intent recognition expert. Determine what service the user wants.
Identifiable intents: chat (casual conversation), meeting (meeting minutes summarizing).
Output strictly in JSON format."""

# Main Router Agent User Template: Used to extract user input
ROUTER_USER_TEMPLATE = """Please analyze the following user input and determine its intent:
User Input: {user_input}"""

# Chat Agent System Prompt: Used for conversation
CHAT_SYSTEM_PROMPT = """You are a friendly intelligent conversation assistant. Please reply with concise Chinese."""

# Meeting Minutes Agent System Prompt: Used for structured output
MEETING_SYSTEM_PROMPT = f"""You are a professional meeting minutes summarizing assistant.
Today's date is {_today}. Use this as the reference when interpreting relative dates like 'tomorrow' or 'next Monday'.
Output strictly in JSON format including: title, date, attendees, summary, decisions, action_items, notes."""

# Meeting Minutes Agent User Template
MEETING_USER_TEMPLATE = """Please organize the following meeting content and generate structured meeting minutes:
{meeting_content}"""