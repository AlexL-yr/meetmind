from typing import Optional, List
from pydantic import BaseModel, Field

class MeetingAction(BaseModel):
    """Meeting Action Item Schema"""
    action: str = Field(..., description="Description of the action item")
    owner: str = Field(..., description="Person responsible for this action")
    deadline: Optional[str] = Field(default=None, description="Deadline for completion")


class MeetingSummary(BaseModel):
    """
    Meeting Minutes Structure
    
    Structured meeting minutes returned after using with_structured_output,
    which can be directly converted into Markdown format.
    
    Attributes:
        title: Meeting title
        date: Meeting date
        attendees: List of attendees
        summary: Executive summary of the meeting main content
        decisions: List of meeting decisions made
        action_items: List of meeting action items
        notes: Meeting additional notes
    """
    title: str = Field(..., description="Meeting title")
    date: str = Field(..., description="Meeting date")
    attendees: List[str] = Field(..., description="List of attendees")
    summary: str = Field(..., description="Executive summary of the meeting main content")
    decisions: List[str] = Field(..., description="List of meeting decisions made")
    action_items: List[MeetingAction] = Field(..., description="List of meeting action items")
    notes: Optional[str] = Field(default=None, description="Meeting additional notes")